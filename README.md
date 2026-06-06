# RTK Token Savings Dashboard

Dashboard web para visualizar estadísticas de ahorro de tokens de [RTK](https://github.com/rtk-ai/rtk) (Rewrite Token Killer), una herramienta de reescritura de prompts que reduce el consumo de tokens en modelos de lenguaje.

## Características

- Estadísticas de ahorro de tokens en tiempo real
- Agrupación de comandos por sesiones (gap de 30 min)
- Detección de sesiones via gateway.log de Hermes
- Soporte para perfiles de Hermes (resolución automática de rutas via `HERMES_HOME`)
- Gráficos interactivos con Chart.js
- API REST completa

## Requisitos

- [RTK](https://github.com/rtk-ai/rtk) instalado y configurado
- Python 3.10+ con FastAPI y Uvicorn
- Acceso a la base de datos `history.db` de RTK (SQLite)

## Instalación

```bash
# Clonar el repo
git clone https://github.com/JaimeCruzH/rtk-dashboard.git
cd rtk-dashboard

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn

# Iniciar el servidor
./start.sh
# o directamente:
python server.py
```

## Configuración

### Ruta de la base de datos

El dashboard resuelve la ruta de `history.db` automáticamente usando `HERMES_HOME`:

1. Si `HERMES_HOME` está definido (modo perfil): `$HERMES_HOME/home/.local/share/rtk/history.db`
2. Fallback: `~/.local/share/rtk/history.db`

Para configurar manualmente:

```bash
# Unix/Linux/macOS
export RTK_DB_PATH="$HOME/.local/share/rtk/history.db"

# Windows
set RTK_DB_PATH="%APPDATA%\\rtk\\history.db"
```

### Detección de sesiones

El dashboard detecta resets de sesión leyendo `gateway.log` de Hermes:
- Ruta: `$HERMES_HOME/logs/gateway.log`
- Los timestamps del gateway están en hora local; se convierten a UTC internamente
- Cache de 60 segundos para evitar releer el log en cada request

## Ejecución como servicio (systemd)

Para ejecutar el dashboard como servicio persistente:

```bash
# Crear archivo de servicio
cat > ~/.config/systemd/user/rtk-dashboard.service << EOF
[Unit]
Description=RTK Token Savings Dashboard
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/jaime/rtk-dashboard
ExecStart=/home/jaime/rtk-dashboard/.venv/bin/python server.py
Restart=always
RestartSec=5
Environment=HERMES_HOME=/home/jaime/.hermes/profiles/programador

[Install]
WantedBy=default.target
EOF

# Recargar y habilitar
systemctl --user daemon-reload
systemctl --user enable rtk-dashboard.service
systemctl --user start rtk-dashboard.service

# Verificar estado
systemctl --user status rtk-dashboard.service
```

## Acceso

Una vez iniciado, el dashboard está disponible en:

- **Local:** `http://localhost:8088/`
- **Remoto:** vía [Tailscale](https://tailscale.com/) (acceso privado a la red local)

> **Nota de seguridad:** Este dashboard es una herramienta interna sin autenticación. No está diseñado para exposición pública. Úsalo únicamente dentro de tu red privada o vía Tailscale.

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

## Formato de números

Los valores de tokens usan separador de miles con punto (locale `es-CL`):

```
1.350.490 tokens ahorrados
```

## Arquitectura

```
rtk-dashboard/
├── server.py          # Backend FastAPI
├── static/
│   └── index.html     # Frontend con Chart.js
├── start.sh           # Script de inicio
├── .venv/             # Entorno virtual Python
└── README.md
```

## Autor

[Jaime Cruz H](https://github.com/JaimeCruzH)

## Licencia

MIT