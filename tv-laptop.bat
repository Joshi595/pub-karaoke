@echo off
rem Pub Karaoke on a laptop at the TV: shows the pub PC's karaoke screen here and plays its sound here.
rem The pub PC keeps the queue, the songs and the phones. This laptop needs only Windows' own ssh, curl and Edge.
rem Once, on this laptop:   ssh-keygen -t ed25519 -N ""
rem Then, on the pub PC:    install-autostart.ps1 -TvLaptopKey <a copy of %USERPROFILE%\.ssh\id_ed25519.pub>
rem That prints what to put in PUB_PC. To start this by itself, put a shortcut to it in shell:startup.
rem PUB_PC: the pub PC's Windows account @ its address. PORT: "port" in the pub PC's settings.json.
rem TV_X: 0 if the TV is this laptop's main (or mirrored) screen, 1920 if it is a second screen to the right.
set "PUB_PC=ACCOUNT@PUB-PC-ADDRESS"
set TV_X=0
set PORT=5000
cd /d "%~dp0"
if "%~1"=="link" goto link
rem Started twice, two TVs would fight over one browser profile: a lock file held open while this runs stops that.
(9>"%TEMP%\pub-karaoke-tv.lock" call :run) 2>nul || echo Pub Karaoke TV is already running. Close its windows to start it again.
exit /b 0

:run
start "Pub Karaoke link to the pub PC - keep this open" /min "%~f0" link
:tv
curl.exe -sf -m 5 -o nul http://127.0.0.1:%PORT%/api/health || (timeout /t 2 /nobreak >nul & goto tv)
start "" /wait msedge --kiosk --no-first-run --autoplay-policy=no-user-gesture-required "--user-data-dir=%LOCALAPPDATA%\PubKaraokeTV" --window-position=%TV_X%,0 http://localhost:%PORT%/tv
timeout /t 5 /nobreak >nul
goto tv

:link
rem Only the TV port comes through. Reconnects by itself after a network drop or a restart of the pub PC.
ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=10 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=accept-new -L %PORT%:127.0.0.1:%PORT% "%PUB_PC%"
timeout /t 5 /nobreak >nul
goto link
