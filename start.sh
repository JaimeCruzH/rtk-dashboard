#!/bin/bash
# RTK Dashboard - Startup script
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec .venv/bin/python3 server.py
