@echo off
setlocal
:: 0F = Clean white text on black background
:: Size is small and compact
mode con cols=55 lines=12
title Sozip Launcher 1.0
color 0F

echo.
echo   =====================================================
echo             S O Z I P   L A U N C H E R
echo   =====================================================
echo.
echo    [ STATUS ] Searching for runtime...

set "PY_EXE=%~dp0sozip_python\python.exe"

:: Check if Python is there
if not exist "%PY_EXE%" (
    color 0C
    echo    [ ERROR  ] 'sozip_python' folder not found.
    echo               Please check your installation.
    echo.
    pause
    exit
)

echo    [ STATUS ] Starting engine...
echo    [ STATUS ] Launcher is now running.
echo.
echo   -----------------------------------------------------
echo      Keep this window open to see game logs/errors.
echo      Minimize it if you want it out of the way.
echo   -----------------------------------------------------
echo.

:: Launch Python but stay in THIS window to show logs
"%PY_EXE%" launcher.py

:: If the launcher closes or crashes, it comes back here
echo.
echo   [ NOTIFICATION ] Launcher has been closed.
echo   Press any key to exit this window.
pause >nul
exit
