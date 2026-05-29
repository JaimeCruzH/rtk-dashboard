# RTK Token Savings Dashboard

Dashboard web para visualizar estadísticas de ahorro de tokens de [RTK](https://github.com/nousresearch/rtk) (Rewrite Token Killer), una herramienta de reescritura de prompts que reduce el consumo de tokens en modelos de lenguaje.

## Demo

> 📸Screenshot pendiente — captura desde `http://localhost:8088/` y guarda como `screenshot.png` en la raíz del proyecto.

## Requisitos

- [RTK](https://github.com/nousresearch/rtk) instalado y configurado
- Python 3.8+ con FastAPI y Uvicorn
- Acceso a la base de datos `history.db` de RTK (SQLite)

## Instalación

```bash
# Clonar el repo
git clone https://github.com/JaimeCruzH/rtk-dashboard.git
cd rtk-dashboard

# Instalar dependencias
pip install fastapi uvicorn

# Iniciar el servidor
./start.sh
# o directamente:
python server.py
```

## Configuración

El dashboard lee de la base de datos de RTK. Asegúrate de que la ruta a `history.db` sea accesible:

```bash
# Unix/Linux/macOS
export RTK_DB_PATH="$HOME/.local/share/rtk/history.db"

# Windows
set RTK_DB_PATH="%APPDATA%\\rtk\\history.db"
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

Una vez iniciado, el dashboard está disponible en:

- **Local:** `http://localhost:8088/`
- **Tailscale:** `http://100.80.61.96:8088/` *(redirección de red configurada)*
- **Dominio:** `http://agentexperto.work:8088/` *(requiere configuración DNS)*

## Formato de números

Los valores de tokens usan separador de miles con punto (locale `es-CL`):

```
1.350.490 tokens ahorrados
```

## Autor

[Jaime Cruz H](https://github.com/JaimeCruzH)

## Licencia

MIT
