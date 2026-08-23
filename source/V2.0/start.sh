#!/usr/bin/env bash
# SOZIP LAUNCHER - Linux Launcher
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ ! -d "venv" ]; then
    echo "[Sozip] Creating virtual environment..."
    python3 -m venv venv
fi

echo "[Sozip] Checking requirements..."
./venv/bin/pip install -r requirements.txt -q

echo "[Sozip] Starting Launcher..."
./venv/bin/python launcher.py
