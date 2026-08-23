@echo off
REM SOZIP LAUNCHER - Windows Launcher
cd /d "%~dp0"

echo [Sozip] Checking requirements...
pip install -r requirements.txt -q

echo [Sozip] Starting Launcher...
python launcher.py
pause
