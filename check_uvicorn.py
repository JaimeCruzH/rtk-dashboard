#!/usr/bin/env python3
"""Check if uvicorn is available"""
import subprocess
result = subprocess.run(["which", "uvicorn"], capture_output=True, text=True)
if result.returncode == 0:
    print(f"UVICORN OK: {result.stdout.strip()}")
else:
    print("NO_UVICORN")
    # Try pip install
    r = subprocess.run(["pip", "install", "fastapi", "uvicorn"], capture_output=True, text=True, timeout=60)
    print(r.stdout[-200:])
    print(r.stderr[-200:])
    # Check again
    r2 = subprocess.run(["which", "uvicorn"], capture_output=True, text=True)
    if r2.returncode == 0:
        print(f"UVICORN OK NOW: {r2.stdout.strip()}")
    else:
        print("STILL NO UVICORN")