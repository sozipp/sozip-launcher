@echo off
setlocal enabledelayedexpansion
title SOZIP LAUNCHER UNIVERSAL 1.0
mode con cols=85 lines=30
color 0B

:: 1. HEADER
echo.
echo    ==========================================================================
echo    #                                                                        #
echo    #            S O Z I P   L A U N C H E R   U N I V E R S A L             #
echo    #                       V E R S I O N   1.0                              #
echo    #                                                                        #
echo    ==========================================================================
echo.

:: 2. FOLDER SELECTOR
echo    [SYSTEM] Please select your installation folder...
set "psCommand=Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; $f.Description = 'Select Sozip Install Folder'; if($f.ShowDialog() -eq 'OK'){ $f.SelectedPath } else { 'CANCEL' }"
for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "%psCommand%"` ) do set "ROOT=%%I"

if "%ROOT%"=="CANCEL" exit

cd /d "%ROOT%"
echo    [SYSTEM] Target: %ROOT%
echo    --------------------------------------------------------------------------

:: 3. LINKS
set "SOZIP_RUNTIME=https://archive.org/download/sozip_python/sozip_python.zip"
set "L_PY=https://sozip19op.github.io/Sozip-launcher/downloads/versions/1.0/Universal/launcher.py"
set "L_BAT=https://sozip19op.github.io/Sozip-launcher/downloads/versions/1.0/Universal/start.bat"
set "L_ICON=https://sozip19op.github.io/Sozip-launcher/images/logo.ico"

:: 4. DOWNLOAD & EXTRACT (Using 3072 for TLS 1.2 compatibility)
echo    [1/4] Downloading Engine (72MB)...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = 3072; (New-Object System.Net.WebClient).DownloadFile('%SOZIP_RUNTIME%', 'runtime.zip')"

echo    [2/4] Extracting Engine...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path 'runtime.zip' -DestinationPath '.\' -Force"
del runtime.zip

echo    [3/4] Downloading Launcher Files...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = 3072; (New-Object System.Net.WebClient).DownloadFile('%L_PY%', 'launcher.py')"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = 3072; (New-Object System.Net.WebClient).DownloadFile('%L_BAT%', 'start.bat')"

echo    [4/4] Downloading Brand Icon...
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol = 3072; (New-Object System.Net.WebClient).DownloadFile('%L_ICON%', 'sozip_icon.ico')"

echo    --------------------------------------------------------------------------
echo    [STATUS] Verification...
if exist ".\sozip_python\python.exe" (
    echo    [SUCCESS] Engine Verified.
) else (
    echo    [!] Checking structure...
    if exist ".\sozip_python\sozip_python\python.exe" (
        xcopy /e /i /y ".\sozip_python\sozip_python\*" ".\sozip_python\"
        rd /s /q ".\sozip_python\sozip_python"
    )
)

echo.
echo    ==========================================================================
echo    #              I N S T A L L A T I O N   C O M P L E T E !               #
echo    #                                                                        #
echo    #           Your launcher is ready in the selected folder.               #
echo    #               Run 'start.bat' to begin your adventure.                 #
echo    #                                                                        #
echo    ==========================================================================
pause
