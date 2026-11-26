# Run once as Administrator on the dedicated pub PC, using its normal kiosk account.
# Server starts at boot under that account with S4U (no saved password); TV starts at interactive login.
# -TvLaptopKey path\to\id_ed25519.pub: the TV is on a laptop at the TV instead (tv-laptop.bat). No TV here; that
# laptop's key may open an SSH link to the local TV port only: no passwords, no commands, no other ports.
# -LaptopTv: the TV is a laptop paired by windows\pub-pc.ps1 (Setup-Pub-PC.bat). No TV here, nothing else to set up.
param([string]$TvLaptopKey, [switch]$LaptopTv)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Run setup.bat first.' }
$taskUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 99 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew
$serverAction = New-ScheduledTaskAction -Execute $taskPython -Argument ('"' + (Join-Path $taskRoot 'run_karaoke.py') + '"') -WorkingDirectory $taskRoot
$serverPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType S4U -RunLevel Limited
Register-ScheduledTask -TaskName 'Pub Karaoke server' -Action $serverAction -Trigger (New-ScheduledTaskTrigger -AtStartup) -Principal $serverPrincipal -Settings $taskSettings -Force | Out-Null
if (-not $TvLaptopKey -and -not $LaptopTv) {
    $tvAction = New-ScheduledTaskAction -Execute $taskPython -Argument ('"' + (Join-Path $taskRoot 'run_karaoke.py') + '" --kiosk') -WorkingDirectory $taskRoot
    $tvPrincipal = New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName 'Pub Karaoke TV' -Action $tvAction -Trigger (New-ScheduledTaskTrigger -AtLogOn -User $taskUser) -Principal $tvPrincipal -Settings $taskSettings -Force | Out-Null
    Write-Output 'Installed. Server starts at boot; TV starts when this account signs in. Reboot to test.'
    return
}
if ($LaptopTv) {
    Unregister-ScheduledTask -TaskName 'Pub Karaoke TV' -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output 'Installed. Server starts at boot; the TV runs on the paired laptop.'
    return
}

# The TV is on a laptop: one public key, one line, nothing that could add a second unrestricted line.
$key = (Get-Content -LiteralPath $TvLaptopKey -Raw).Trim()
if ($key -notmatch '^(ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(256|384|521)) [A-Za-z0-9+/]+={0,3}( [^\r\n"]*)?$') {
    throw 'Not an SSH public key. Give the .pub file that ssh-keygen made on the TV laptop.'
}
$port = 5000
$settingsFile = Join-Path $taskRoot 'settings.json'
if (Test-Path -LiteralPath $settingsFile) {
    $configured = (Get-Content -LiteralPath $settingsFile -Raw -Encoding UTF8 | ConvertFrom-Json).port
    if ($configured) { $port = [int]$configured }
}
Unregister-ScheduledTask -TaskName 'Pub Karaoke TV' -Confirm:$false -ErrorAction SilentlyContinue

if ((Get-WindowsCapability -Online -Name 'OpenSSH.Server*').State -ne 'Installed') {
    Add-WindowsCapability -Online -Name 'OpenSSH.Server~~~~0.0.1.0' | Out-Null
}
Set-Service -Name sshd -StartupType Automatic
Start-Service -Name sshd  # first start writes sshd_config and the host keys
$sshDir = Join-Path $env:ProgramData 'ssh'
$sshConfig = Join-Path $sshDir 'sshd_config'
$lines = @(Get-Content -LiteralPath $sshConfig)
if ($lines -notcontains 'PasswordAuthentication no') {  # first value wins in sshd_config, so it goes on top
    Set-Content -LiteralPath $sshConfig -Value (@('PasswordAuthentication no') + $lines) -Encoding ASCII
}
# This account is an administrator (the script runs elevated), so sshd reads its keys from this file.
$keysFile = Join-Path $sshDir 'administrators_authorized_keys'
$entry = "restrict,port-forwarding,permitopen=`"127.0.0.1:$port`",command=`"exit`" $key"
if (-not (Test-Path -LiteralPath $keysFile) -or @(Get-Content -LiteralPath $keysFile) -notcontains $entry) {
    Add-Content -LiteralPath $keysFile -Value $entry -Encoding ASCII
}
icacls.exe $keysFile /inheritance:r /grant '*S-1-5-32-544:F' '*S-1-5-18:F' | Out-Null  # Administrators, SYSTEM
if ($LASTEXITCODE) { throw "icacls could not protect $keysFile" }
$rule = Get-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -ErrorAction SilentlyContinue
if ($rule) {
    $rule | Set-NetFirewallRule -Profile Private
} else {
    New-NetFirewallRule -Name 'OpenSSH-Server-In-TCP' -DisplayName 'OpenSSH Server (sshd)' -Direction Inbound -Protocol TCP -LocalPort 22 -Action Allow -Profile Private | Out-Null
}
Restart-Service -Name sshd
Write-Output 'Installed. Server starts at boot; the TV runs on the laptop with tv-laptop.bat. Reboot to test.'
Write-Output ("In tv-laptop.bat on the TV laptop, set PUB_PC=" + $taskUser.Split('\')[-1] + "@" + $env:COMPUTERNAME + " (or this PC's fixed IP address instead of its name).")
Write-Output 'This PC''s network must be Private (Settings > Network): the SSH link is allowed on private networks only.'
