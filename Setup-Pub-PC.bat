@echo off
setlocal
set "KARAOKE_INSTALLER=%~f0"
rem One administrator prompt for everything: installs, start at boot, firewall. Same account, same desktop.
net session >nul 2>&1 || (powershell.exe -NoProfile -Command "Start-Process -Verb RunAs -FilePath $env:KARAOKE_INSTALLER" || (echo Setup needs the administrator prompt approved. & pause) & exit /b)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$text=[IO.File]::ReadAllText($env:KARAOKE_INSTALLER); & ([scriptblock]::Create(($text -split '(?m)^::POWERSHELL\r?$',2)[1]))"
if errorlevel 1 (echo Setup stopped. Fix the problem above and run this file again. & pause & exit /b 1)
pause
exit /b 0
::POWERSHELL
$ErrorActionPreference = 'Stop'
$source = Split-Path -LiteralPath $env:KARAOKE_INSTALLER
$localSetup = Join-Path $source 'windows\pub-pc.ps1'
if (Test-Path -LiteralPath $localSetup) { & $localSetup; return }
$target = Join-Path $env:LOCALAPPDATA 'PubKaraoke\App'
$zip = Join-Path ([IO.Path]::GetTempPath()) (([guid]::NewGuid()).ToString() + '.zip')
try {
    if ($text -match '(?m)^# PUBPACKAGE ([0-9a-f]{64}) ([A-Za-z0-9+/=]+)\r?$') {
        $digest = $Matches[1]
        [IO.File]::WriteAllBytes($zip,[Convert]::FromBase64String($Matches[2]))
    } else {
        $release = Invoke-RestMethod 'https://api.github.com/repos/Joshi595/pub-karaoke/releases/latest'
        $asset = $release.assets | Where-Object name -eq 'pub-karaoke-windows.zip' | Select-Object -First 1
        if (-not $asset -or $asset.digest -notmatch '^sha256:([a-f0-9]{64})$') { throw 'Download the bundled Setup-Pub-PC.bat, or unzip the project and run Setup-Pub-PC.bat inside it.' }
        $digest = $Matches[1]
        Invoke-WebRequest -UseBasicParsing $asset.browser_download_url -OutFile $zip
    }
    if ((Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash -ne $digest) { throw 'The application package checksum did not match. Download it again.' }
    $stage = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
    Expand-Archive -LiteralPath $zip -DestinationPath $stage
    $null = New-Item -ItemType Directory -Path $target -Force
    foreach ($file in Get-ChildItem -LiteralPath $stage -Recurse -File) {
        $relative = $file.FullName.Substring($stage.Length + 1)
        $destination = Join-Path $target $relative
        if ($relative -eq 'starter-songs.txt' -and (Test-Path -LiteralPath $destination)) { continue }
        $null = [IO.Directory]::CreateDirectory((Split-Path -LiteralPath $destination))
        Copy-Item -LiteralPath $file.FullName -Destination $destination -Force
    }
    & (Join-Path $target 'windows\pub-pc.ps1')
} finally {
    Remove-Item -LiteralPath $zip -Force -ErrorAction SilentlyContinue
    if ($stage -and (Split-Path -Parent $stage) -eq ([IO.Path]::GetTempPath()).TrimEnd('\') -and (Split-Path -Leaf $stage) -match '^[a-f0-9-]{36}$') {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
