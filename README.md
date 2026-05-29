# RTK Token Savings Dashboard

Dashboard web para visualizar estadísticas de ahorro de tokens de [RTK](https://github.com/nousresearch/rtk) (Rewrite Token Killer),una herramienta de reescritura de prompts que reduce el consumo de tokens en modelos de lenguaje.

## Demo

![Dashboard Screenshot](https://raw.githubusercontent.com/JaimeCruzH/rtk-dashboard/main/screenshot.png)

## Stack

- **Backend:** FastAPI (Python)
- **Frontend:** Chart.js con tema oscuro
- **Datos:** SQLite (`history.db` de RTK)
- **Servidor:** Uvicorn, puerto 8088

## Instalación

```bash
cd /opt/data/rtk-dashboard
./start.sh
# o directamente:
/opt/hermes/.venv/bin/python server.py
```

## API Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/summary` | Totales: comandos, tokens procesados, ahorro %, fallos |
| `GET /api/daily` | Desglose diario de tokens y ahorro |
| `GET /api/sessions` | Comandos agrupados en sesiones (gap 30 min) |
| `GET /api/range?from=Y-m-d&to=Y-m-d` | Estadísticas filtradas por rango de fechas |
| `GET /api/top-commands?n=10` | Top N comandos por tokens ahorrados |
| `GET /api/failures?limit=20` | Log de fallos de parsing |
| `GET /api/commands?limit=50&offset=0&sort=timestamp&order=desc` | Lista paginada de comandos |
| `GET /api/tokens-by-day` | Tokens por día (para gráfico apilado) |

## Acceso

- **Local:** `http://localhost:8088/`
- **Tailscale:** `http://100.80.61.96:8088/`
- **Dominio:** `http://agentexperto.work:8088/`

## Formato de números

Los valores de tokens usan separador de miles con punto (locale `es-CL`):

```
1.350.490 tokens ahorrados
```

## Autor

[Jaime Cruz H](https://github.com/JaimeCruzH)

## Licencia

MIT
