@echo off
setlocal
set "PUB_TV_FILE=%~f0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $lines=[IO.File]::ReadAllLines($env:PUB_TV_FILE); $tmp=Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid()); $null=New-Item -ItemType Directory -Path $tmp; $script=Join-Path $tmp 'laptop.ps1'; $kit=Join-Path $tmp 'pair.json'; try { [IO.File]::WriteAllBytes($script,[Convert]::FromBase64String($lines[-2])); [IO.File]::WriteAllBytes($kit,[Convert]::FromBase64String($lines[-1])); & $script -PairFile $kit } finally { Remove-Item -LiteralPath $script,$kit -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue }"
if errorlevel 1 (echo TV setup stopped. Check the message above and run this file again. & pause & exit /b 1)
exit /b 0
