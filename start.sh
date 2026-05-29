#!/bin/bash
# RTK Dashboard - Startup script
# Se ejecuta con: bash /opt/data/rtk-dashboard/start.sh
# Acceso web: http://IP_DEL_VPS:8088
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec /opt/hermes/.venv/bin/python3 server.py
