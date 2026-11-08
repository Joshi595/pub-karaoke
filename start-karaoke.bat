@echo off
rem Pub Karaoke: starts the server and opens the karaoke screen full-screen on the TV.
rem Safe to double-click again: a healthy server and its dedicated TV profile are reused.
rem TV_X: 0 if the TV is the laptop's main (or mirrored) screen, 1920 if it is a second screen to the right.
set TV_X=0
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (echo Run setup.bat first. & pause & exit /b 1)
.venv\Scripts\python.exe run_karaoke.py --status >nul 2>&1
if errorlevel 1 start "Pub Karaoke server - keep this open" /min .venv\Scripts\python.exe run_karaoke.py
.venv\Scripts\python.exe run_karaoke.py --wait
if errorlevel 1 (pause & exit /b 1)
start "Pub Karaoke TV - keep this open" /min .venv\Scripts\python.exe run_karaoke.py --kiosk
