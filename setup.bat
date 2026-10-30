@echo off
rem Pub Karaoke setup for Windows: double-click once. Installs what's missing (with winget), the live app, and
rem (if you say yes) the song maker. Safe to run again: it skips what is already there.
rem   setup.bat /nomaker   skips the song maker question
setlocal
cd /d "%~dp0"
rem Exact versions known to work together. With an NVIDIA card: CUDA 12.6 builds; onnxruntime-gpu 1.27+ needs CUDA 13
rem (NVIDIA driver 580+), while 1.26 uses the CUDA 12 files that come with torch.
set "TORCH=torch==2.14.1 torchaudio==2.11.0"
set "SEPARATOR=0.47.1"

where winget >nul 2>&1 || (echo winget is missing: install "App Installer" from the Microsoft Store, then run setup.bat again. & goto :fail)

call :findpy
if not defined PY (
  echo Installing Python 3.12...
  winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
  call :findpy
)
if not defined PY (echo Python 3.12 is installed. Close this window and run setup.bat again. & goto :fail)
echo Python: %PY%

where cloudflared >nul 2>&1 || if not exist tools\cloudflared.exe (
  echo Installing cloudflared, for the internet link...
  winget install -e --id Cloudflare.cloudflared --accept-package-agreements --accept-source-agreements
)

echo Setting up the live app...
if not exist .venv\Scripts\python.exe ("%PY%" -m venv .venv || goto :fail)
.venv\Scripts\python -m pip install --disable-pip-version-check -q --upgrade pip || goto :fail
.venv\Scripts\python -m pip install --disable-pip-version-check -r requirements.txt || goto :fail
.venv\Scripts\python -c "import app; app.ensure_settings('.')" || goto :fail

if /i "%~1"=="/nomaker" goto :shortcut
echo.
echo The song maker turns any song a guest picks into karaoke (about 5 GB, with the AI models).
choice /c YN /m "Install the song maker"
if errorlevel 2 goto :shortcut

where ffmpeg >nul 2>&1 || winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
where node >nul 2>&1 || winget install -e --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
if not exist .venv-maker\Scripts\python.exe ("%PY%" -m venv .venv-maker || goto :fail)
set "PIP=.venv-maker\Scripts\python -m pip install --disable-pip-version-check"
%PIP% -q --upgrade pip || goto :fail
where nvidia-smi >nul 2>&1 && (
  echo NVIDIA graphics card found: installing the fast version.
  %PIP% %TORCH% --index-url https://download.pytorch.org/whl/cu126 || goto :fail
  %PIP% -r requirements-maker.txt "audio-separator[gpu]==%SEPARATOR%" "onnxruntime-gpu<1.27" || goto :fail
) || (
  echo No NVIDIA graphics card: installing the version for the processor. Songs take longer to make.
  %PIP% %TORCH% --index-url https://download.pytorch.org/whl/cpu || goto :fail
  %PIP% -r requirements-maker.txt "audio-separator[cpu]==%SEPARATOR%" || goto :fail
)

:shortcut
powershell -NoProfile -Command "$s = (New-Object -ComObject WScript.Shell).CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Pub Karaoke.lnk'); $s.TargetPath = '%~dp0start-karaoke.bat'; $s.WorkingDirectory = '%~dp0'; $s.Save()"
echo.
echo Done. Double-click "Pub Karaoke" on the desktop to start. The staff PIN is in settings.json.
pause
exit /b 0

:findpy
set "PY="
for /f "delims=" %%p in ('py -3.12 -c "import sys; print(sys.executable)" 2^>nul') do set "PY=%%p"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
exit /b 0

:fail
echo.
echo Setup stopped. Fix the problem above, then run setup.bat again.
pause
exit /b 1
