#!/usr/bin/env python3
"""
RTK Dashboard - Servidor FastAPI
Lee la base history.db de RTK y expone endpoints REST
para el frontend de estadísticas.
"""
import sqlite3
import os
import zoneinfo
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles

TZ = zoneinfo.ZoneInfo("America/Santiago")
UTC = zoneinfo.ZoneInfo("UTC")

def utc_to_local_date(ts_str):
    """Convierte timestamp UTC (string ISO) a fecha local YYYY-MM-DD en America/Santiago"""
    if not ts_str:
        return None
    clean = ts_str.replace('Z', '').replace(' ', 'T')
    if '.' in clean:
        clean = clean.split('.')[0]
    dt_utc = datetime.fromisoformat(clean).replace(tzinfo=UTC)
    return dt_utc.astimezone(TZ).strftime("%Y-%m-%d")

app = FastAPI(title="RTK Dashboard")

DB_PATH = os.path.expanduser("~/.local/share/rtk/history.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/api/summary")
def get_summary():
    """Estadísticas generales: total tokens, ahorro, comandos, tiempo de ejecución"""
    conn = get_connection()
    cur = conn.cursor()
    
    # Total de comandos
    cur.execute("SELECT COUNT(*) FROM commands")
    total_commands = cur.fetchone()[0]
    
    # Totales de tokens
    cur.execute("""
        SELECT 
            COALESCE(SUM(input_tokens), 0),
            COALESCE(SUM(output_tokens), 0),
            COALESCE(SUM(saved_tokens), 0),
            COALESCE(SUM(exec_time_ms), 0)
        FROM commands
    """)
    row = cur.fetchone()
    total_input = row[0]
    total_output = row[1]
    total_saved = row[2]
    total_time_ms = row[3]
    
    # Fallos de parseo
    cur.execute("SELECT COUNT(*) FROM parse_failures")
    total_failures = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM parse_failures WHERE fallback_succeeded = 1")
    auto_recovered = cur.fetchone()[0]
    
    # Primer y último comando
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM commands")
    first_seen, last_seen = cur.fetchone()
    
    conn.close()
    
    # Porcentaje agregado real (sobre original = input + saved)
    total_original = total_input + total_saved
    real_savings_pct = round(total_saved / total_original * 100, 2) if total_original > 0 else 0.0

    return {
        "total_commands": total_commands,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_saved_tokens": total_saved,
        "avg_savings_pct": real_savings_pct,
        "total_time_ms": total_time_ms,
        "total_failures": total_failures,
        "auto_recovered_failures": auto_recovered,
        "first_seen": first_seen,
        "last_seen": last_seen
    }

@app.get("/api/daily")
def get_daily():
    """Desglose por día (en zona horaria America/Santiago)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM commands ORDER BY timestamp")
    rows = cur.fetchall()
    conn.close()

    daily = defaultdict(lambda: {
        "commands": 0, "input_tokens": 0, "output_tokens": 0,
        "saved_tokens": 0, "total_time_ms": 0
    })

    for r in rows:
        cmd = dict(r)
        day = utc_to_local_date(cmd["timestamp"])
        if not day:
            continue
        d = daily[day]
        d["commands"] += 1
        d["input_tokens"] += cmd.get("input_tokens", 0) or 0
        d["output_tokens"] += cmd.get("output_tokens", 0) or 0
        d["saved_tokens"] += cmd.get("saved_tokens", 0) or 0
        d["total_time_ms"] += cmd.get("exec_time_ms", 0) or 0

    result = []
    for day in sorted(daily.keys()):
        d = daily[day]
        original = d["input_tokens"] + d["saved_tokens"]
        avg_pct = round(d["saved_tokens"] / original * 100, 2) if original > 0 else 0.0
        result.append({
            "day": day,
            "commands": d["commands"],
            "input_tokens": d["input_tokens"],
            "output_tokens": d["output_tokens"],
            "saved_tokens": d["saved_tokens"],
            "avg_savings_pct": avg_pct,
            "total_time_ms": d["total_time_ms"]
        })

    return result

@app.get("/api/tokens-by-day")
def get_tokens_by_day():
    """Por día: tokens originales vs comprimidos (zona America/Santiago)"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM commands ORDER BY timestamp")
    rows = cur.fetchall()
    conn.close()

    daily = defaultdict(lambda: {
        "commands": 0, "original_tokens": 0, "compressed_tokens": 0,
        "saved_tokens": 0, "savings_count": 0, "savings_sum": 0.0
    })

    for r in rows:
        cmd = dict(r)
        day = utc_to_local_date(cmd["timestamp"])
        if not day:
            continue
        d = daily[day]
        inp = cmd.get("input_tokens", 0) or 0
        saved = cmd.get("saved_tokens", 0) or 0
        d["commands"] += 1
        d["original_tokens"] += inp + saved
        d["compressed_tokens"] += inp
        d["saved_tokens"] += saved

    result = []
    for day in sorted(daily.keys()):
        d = daily[day]
        avg_pct = round(d["saved_tokens"] / d["original_tokens"] * 100, 2) if d["original_tokens"] > 0 else 0.0
        result.append({
            "day": day,
            "original_tokens": d["original_tokens"],
            "compressed_tokens": d["compressed_tokens"],
            "saved_tokens": d["saved_tokens"],
            "commands": d["commands"],
            "avg_savings_pct": avg_pct
        })

    return result

GATEWAY_LOG = os.path.expanduser("~/.hermes/logs/gateway.log")
SESSION_TIMEOUT = 1800  # 30 min en segundos

# Cache para session resets del gateway (TTL 60s)
_session_resets_cache = {"data": None, "ts": 0.0}

def load_session_resets():
    """Lee gateway.log y extrae timestamps de session_reset para el chat actual.
    Los timestamps del log están en UTC (misma zona que RTK).
    Resultado cacheado 60 segundos para no releer el log en cada request."""
    import time
    now = time.monotonic()
    if _session_resets_cache["data"] is not None and now - _session_resets_cache["ts"] < 60:
        return _session_resets_cache["data"]

    resets = []
    if not os.path.isfile(GATEWAY_LOG):
        return resets
    try:
        with open(GATEWAY_LOG) as f:
            for line in f:
                if "session_reset" not in line:
                    continue
                parts = line.strip().split()
                if len(parts) < 2:
                    continue
                # Formato: "2026-05-26 22:23:23,038 INFO ..."
                ts_str = f"{parts[0]} {parts[1].split(',')[0]}"
                try:
                    dt = datetime.fromisoformat(ts_str).replace(tzinfo=UTC)
                    resets.append(dt)
                except ValueError:
                    continue
    except Exception:
        pass
    resets = sorted(resets)
    _session_resets_cache["data"] = resets
    _session_resets_cache["ts"] = now
    return resets

# ── Funciones de consulta ────────────────────────────────────────────

@app.get("/api/sessions")
def get_sessions():
    """
    Agrupa comandos en sesiones usando dos criterios:
    1. Session resets del gateway (/new en Hermes) como límite primario
    2. Gap de 30 min entre comandos consecutivos como respaldo
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM commands ORDER BY timestamp")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return []

    # Cargar resets del gateway
    resets = load_session_resets()
    reset_idx = 0
    
    sessions = []
    current = []
    prev_ts = None
    session_counter = 0

    for r in rows:
        cmd = dict(r)
        ts = datetime.fromisoformat(cmd["timestamp"])
        
        # ¿Este comando cruza un session_reset?
        crossed_reset = False
        while reset_idx < len(resets) and ts > resets[reset_idx]:
            crossed_reset = True
            reset_idx += 1
        
        # ¿Hay gap de 30 min desde el comando anterior?
        gap_long = False
        if prev_ts is not None and not crossed_reset:
            gap = (ts - prev_ts).total_seconds()
            if gap > SESSION_TIMEOUT:
                gap_long = True
        
        if crossed_reset or gap_long:
            if current:
                sessions.append(build_session(current, session_counter))
                session_counter += 1
            current = []
        
        current.append(cmd)
        prev_ts = ts

    if current:
        sessions.append(build_session(current, session_counter))

    return sessions

def build_session(commands, idx):
    """Convierte una lista de comandos en un objeto de sesión resumido"""
    first = commands[0]
    last = commands[-1]
    
    total_saved = sum(c["saved_tokens"] for c in commands)
    total_input = sum(c["input_tokens"] for c in commands)
    total_output = sum(c["output_tokens"] for c in commands)
    total_time = sum(c["exec_time_ms"] for c in commands)
    
    total_original = total_input + total_saved
    if total_original > 0:
        pct = round(total_saved / total_original * 100, 2)
    else:
        pct = 0.0
    
    return {
        "session_id": f"{first['timestamp'][:19]}_{idx}",
        "start": first["timestamp"],
        "end": last["timestamp"],
        "total_commands": len(commands),
        "input_tokens": total_input,
        "output_tokens": total_output,
        "saved_tokens": total_saved,
        "savings_pct": pct,
        "total_time_ms": total_time,
        "top_commands": [c["rtk_cmd"] for c in commands[:5]],
        "project": first.get("project_path", "") or "default"
    }

@app.get("/api/range")
def get_range(
    from_date: str = Query(None, alias="from"),
    to_date: str = Query(None, alias="to"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    """Comandos filtrados por rango de fechas (fechas locales America/Santiago)
    con estadísticas agregadas"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM commands ORDER BY timestamp")
    rows = cur.fetchall()
    conn.close()
    
    # Filtrar por fecha local (America/Santiago)
    commands = []
    for r in rows:
        cmd = dict(r)
        day = utc_to_local_date(cmd["timestamp"])
        if not day:
            continue
        if from_date and day < from_date:
            continue
        if to_date and day > to_date:
            continue
        commands.append(cmd)
    
    total_saved = sum(c["saved_tokens"] for c in commands)
    total_input = sum(c["input_tokens"] for c in commands)
    total_output = sum(c["output_tokens"] for c in commands)
    total_time = sum(c["exec_time_ms"] for c in commands)
    
    total_original = total_input + total_saved
    pct = round(total_saved / total_original * 100, 2) if total_original > 0 else 0
    
    return {
        "summary": {
            "total_commands": len(commands),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_saved_tokens": total_saved,
            "avg_savings_pct": pct,
            "total_time_ms": total_time
        },
        "total": len(commands),
        "limit": limit,
        "offset": offset,
        "commands": [
            {
                "id": c["id"],
                "timestamp": c["timestamp"],
                "original_cmd": c["original_cmd"],
                "rtk_cmd": c["rtk_cmd"],
                "input_tokens": c["input_tokens"],
                "output_tokens": c["output_tokens"],
                "saved_tokens": c["saved_tokens"],
                "savings_pct": c["savings_pct"],
                "exec_time_ms": c["exec_time_ms"]
            }
            for c in commands[offset:offset + limit]
        ]
    }

@app.get("/api/top-commands")
def get_top_commands(n: int = Query(10, ge=1, le=100)):
    """Top N comandos por tokens ahorrados"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            original_cmd,
            COUNT(*) as times_used,
            SUM(input_tokens) as input_tokens,
            SUM(output_tokens) as output_tokens,
            SUM(saved_tokens) as saved_tokens,
            ROUND(SUM(saved_tokens) * 100.0 / NULLIF(SUM(input_tokens) + SUM(saved_tokens), 0), 2) as avg_savings_pct,
            SUM(exec_time_ms) as total_time_ms
        FROM commands
        GROUP BY original_cmd
        ORDER BY saved_tokens DESC
        LIMIT ?
    """, (n,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/failures")
def get_failures(limit: int = Query(20, ge=1, le=100)):
    """Registro de fallos de parseo"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM parse_failures
        ORDER BY timestamp DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

@app.get("/api/commands")
def get_commands(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("timestamp", pattern="^(timestamp|saved_tokens|savings_pct)$"),
    order: str = Query("desc", pattern="^(asc|desc)$")
):
    """Lista paginada de comandos"""
    conn = get_connection()
    cur = conn.cursor()
    
    direction = "DESC" if order == "desc" else "ASC"
    cur.execute(f"""
        SELECT * FROM commands
        ORDER BY {sort} {direction}
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = cur.fetchall()
    
    cur.execute("SELECT COUNT(*) FROM commands")
    total = cur.fetchone()[0]
    
    conn.close()
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "commands": [dict(r) for r in rows]
    }

# Servir el frontend estático
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    print(f"🚀 RTK Dashboard iniciando en http://0.0.0.0:8088")
    print(f"📊 Datos desde: {DB_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8088)