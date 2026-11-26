# The pub PC: karaoke server and song maker, started at boot. The TV is a laptop at the TV, paired with the
# Connect-Karaoke-TV.bat this puts on the desktop. Setup-Pub-PC.bat runs it as administrator, for the signed-in account.
# Safe to run again: songs, settings and the paired laptop stay. Each run makes a fresh one-time pairing file.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$python = Join-Path $root '.venv\Scripts\python.exe'
function Assert-Exit([string]$what) { if ($LASTEXITCODE) { throw "$what failed (exit code $LASTEXITCODE)." } }

# A running server or song maker keeps its files open, and pip can't replace them.
Stop-ScheduledTask -TaskName 'Pub Karaoke server' -ErrorAction SilentlyContinue
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object { $_.CommandLine -like "*$root*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Write-Host 'Installing the karaoke app and the song maker. The first time this takes 15 to 30 minutes.'
& cmd.exe /c setup.bat /pub; Assert-Exit 'Installing the app'
Write-Host 'Downloading the song maker''s AI models (about 2 GB the first time)...'
& (Join-Path $root '.venv-maker\Scripts\python.exe') make_songs.py --prepare-models; Assert-Exit 'Downloading the models'
& $python run_karaoke.py --prepare; Assert-Exit 'Preparing the settings'  # replaces the default PIN

$settings = Get-Content -LiteralPath (Join-Path $root 'settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$port = if ($settings.port) { [int]$settings.port } else { 5000 }
$guestPort = if ($settings.guest_port) { [int]$settings.guest_port } else { 5001 }

# Guests' phones (guest port) and the TV laptop (5022) come in from the venue network: allowed on private networks.
Remove-NetFirewallRule -Name 'PubKaraoke-In' -ErrorAction SilentlyContinue
New-NetFirewallRule -Name 'PubKaraoke-In' -DisplayName 'Pub Karaoke (guests and TV laptop)' -Direction Inbound `
    -Protocol TCP -LocalPort @($guestPort, 5022) -Action Allow -Profile Private, Domain | Out-Null
foreach ($network in @(Get-NetConnectionProfile | Where-Object NetworkCategory -eq 'Public')) {
    $answer = Read-Host ("This PC's network '" + $network.Name + "' is Public, so the TV laptop and phones can't reach it. Make it Private? [Y/n]")
    if ($answer -notmatch '^[nN]') { Set-NetConnectionProfile -InterfaceIndex $network.InterfaceIndex -NetworkCategory Private }
}

& (Join-Path $root 'install-autostart.ps1') -LaptopTv
$pairFile = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Connect-Karaoke-TV.bat'
& $python tv_link.py $pairFile; Assert-Exit 'Making the TV laptop file'
Start-ScheduledTask -TaskName 'Pub Karaoke server'

Write-Host 'Starting karaoke...'
$ok = $false
foreach ($second in 1..90) {
    try { $ok = (Invoke-RestMethod "http://127.0.0.1:$port/api/health" -TimeoutSec 2).ok } catch { Start-Sleep -Seconds 1 }
    if ($ok) { break }
}
if (-not $ok) { throw 'The karaoke server did not start. See logs\supervisor.log in ' + $root }
$address = (& $python -c "import app; print(app.lan_ip())").Trim()
Write-Host ''
Write-Host '======================================================================' -ForegroundColor Green
Write-Host ' Pub Karaoke is set up. It starts by itself whenever this PC is on.' -ForegroundColor Green
Write-Host ''
Write-Host (" Staff page (phone on the staff Wi-Fi): http://" + $address + ":" + $guestPort + "/admin")
Write-Host (" Staff PIN: " + $settings.pin)
Write-Host ''
Write-Host ' Next: copy Connect-Karaoke-TV.bat from this desktop to a USB stick and double-click it on the'
Write-Host ' laptop at the TV. It works once, within 24 hours: run Setup-Pub-PC.bat again for a new one.'
Write-Host '======================================================================' -ForegroundColor Green
