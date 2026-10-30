@echo off
rem Pub Karaoke: starts the server and opens the karaoke screen full-screen on the TV.
rem Safe to double-click again at any time: it closes the old server and TV screen first; the queue is kept.
rem TV_X: 0 if the TV is the laptop's main (or mirrored) screen, 1920 if it is a second screen to the right.
set TV_X=0
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run setup.bat first. & pause & exit /b 1)
set PORT=5000
for /f "delims=" %%p in ('.venv\Scripts\python -c "import json; print(json.load(open('settings.json', encoding='utf-8-sig')).get('port', 5000))" 2^>nul') do set PORT=%%p
taskkill /fi "WINDOWTITLE eq Pub Karaoke server*" /t /f >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"name='msedge.exe'\" | Where-Object { $_.CommandLine -like '*.tv-profile*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1
timeout /t 1 /nobreak >nul
start "Pub Karaoke server - keep this open" /min .venv\Scripts\python.exe app.py
timeout /t 3 /nobreak >nul
start "" msedge --kiosk http://localhost:%PORT%/tv --edge-kiosk-type=fullscreen --no-first-run --autoplay-policy=no-user-gesture-required --user-data-dir="%~dp0.tv-profile" --window-position=%TV_X%,0
