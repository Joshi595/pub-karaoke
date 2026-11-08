# Run once as Administrator on the dedicated pub PC, using its normal kiosk account.
# Server starts at boot under that account with S4U (no saved password); TV starts at interactive login.
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup.bat first.' }
$taskUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$serverAction = New-ScheduledTaskAction -Execute $taskPython -Argument ('"' + (Join-Path $taskRoot 'run_karaoke.py') + '"') -WorkingDirectory $taskRoot
$serverPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType S4U -RunLevel Limited
Register-ScheduledTask -TaskName 'Pub Karaoke server' -Action $serverAction -Trigger (New-ScheduledTaskTrigger -AtStartup) -Principal $serverPrincipal -Settings $taskSettings -Force | Out-Null
$tvAction = New-ScheduledTaskAction -Execute $taskPython -Argument ('"' + (Join-Path $taskRoot 'run_karaoke.py') + '" --kiosk') -WorkingDirectory $taskRoot
$tvPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Pub Karaoke TV' -Action $tvAction -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $taskUser) -Principal $tvPrincipal -Settings $taskSettings -Force | Out-Null
Write-Output 'Installed. Server starts at boot; TV starts when this account signs in. Reboot to test.'
