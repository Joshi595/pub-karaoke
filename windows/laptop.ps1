param([string]$PairFile)
$ErrorActionPreference = 'Stop'
$playerDir = Join-Path $env:LOCALAPPDATA 'PubKaraokeTV'
$null = New-Item -ItemType Directory -Path $playerDir -Force
Set-Location -LiteralPath $playerDir
$configFile = Join-Path $playerDir 'player.json'
$installedScript = Join-Path $playerDir 'laptop.ps1'
$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe",
          "$env:LOCALAPPDATA\Microsoft\Edge\Application\msedge.exe") | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $edge -and $PairFile) {
    & winget install --id Microsoft.Edge -e --accept-source-agreements --accept-package-agreements
    if ($LASTEXITCODE -eq 0) { & $PSCommandPath -PairFile $PairFile; return }
}
if (-not $edge) { throw 'Microsoft Edge is required. Install Edge and reopen the TV installer.' }
$sshDir = Join-Path $env:SystemRoot 'System32\OpenSSH'
$ssh = Join-Path $sshDir 'ssh.exe'
if (-not (Test-Path -LiteralPath $ssh) -and $PairFile) {
    $install = Start-Process powershell.exe -Verb RunAs -Wait -PassThru -ArgumentList '-NoProfile -Command "Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0 -ErrorAction Stop"'
    if ($install.ExitCode) { throw 'Could not install the Windows OpenSSH client.' }
}
if (-not (Test-Path -LiteralPath $ssh)) { throw 'Windows OpenSSH Client is missing. Rerun the TV installer.' }

function Get-LinkOptions($config) {
    # Local paths are relative to the private player directory, including when its name contains spaces.
    @('-F','NUL','-p',[string]$config.ssh_port,'-i','player_key','-o','IdentitiesOnly=yes',
      '-o','BatchMode=yes','-o','ConnectTimeout=4','-o','StrictHostKeyChecking=yes',
      '-o','GlobalKnownHostsFile=NUL','-o',("UserKnownHostsFile=" + $config.known_hosts),
      '-o','HostKeyAlias=pub-karaoke','-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2')
}
function Set-PlayerShortcut($folder, $name, [bool]$hiddenWindow) {
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut((Join-Path $folder ($name + '.lnk')))
    $shortcut.TargetPath = (Get-Command powershell.exe).Source
    $shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $installedScript + '"'
    $shortcut.WorkingDirectory = $playerDir
    if ($hiddenWindow) { $shortcut.WindowStyle = 7 }
    $shortcut.Save()
}
if ($PairFile) {
    $kit = Get-Content -Raw -LiteralPath $PairFile | ConvertFrom-Json
    if (-not (Test-Path -LiteralPath 'player_key')) {
        & (Join-Path $sshDir 'ssh-keygen.exe') -q -t ed25519 -N '""' -f player_key
        if ($LASTEXITCODE) { throw 'Could not create a private key for this laptop.' }
    }
    $pinFile = 'host-' + ([guid]::NewGuid().ToString('N'))
    Set-Content -LiteralPath $pinFile -Encoding ASCII -Value ("pub-karaoke " + $kit.host_key)
    $kit | Add-Member -NotePropertyName known_hosts -NotePropertyValue $pinFile
    $options = Get-LinkOptions $kit
    $connected = $false
    foreach ($address in @($kit.host,$kit.address) | Select-Object -Unique) {
        if (-not $address -or $address -eq '127.0.0.1') { continue }
        foreach ($account in @('tv',('pair-' + $kit.ticket))) {
            $reply = & $ssh @options -n -l $account $address check
            if ($LASTEXITCODE -eq 0 -and $reply -eq 'Pub Karaoke TV') { $connected = $true; break }
        }
        if ($connected) { break }
    }
    if (-not $connected) {
        Remove-Item -LiteralPath $pinFile
        throw 'Pairing failed. Check the staff network and that the PC is on. For an expired or used USB file, run Setup-Pub-PC.bat again.'
    }
    $kit.PSObject.Properties.Remove('ticket')
    Add-Type -AssemblyName System.Windows.Forms
    $screens = @([Windows.Forms.Screen]::AllScreens)
    $index = 0
    if ($screens.Count -gt 1) {
        for ($i=0; $i -lt $screens.Count; $i++) {
            Write-Host ("{0}. {1}  {2}" -f ($i+1),$screens[$i].DeviceName,$screens[$i].Bounds)
        }
        do { $selection = Read-Host 'Display number for the TV' } until ($selection -match '^\d+$' -and [int]$selection -in (1..$screens.Count))
        $index = [int]$selection - 1
    }
    $kit | Add-Member -NotePropertyName screen -NotePropertyValue $screens[$index].DeviceName
    $kit | ConvertTo-Json | Set-Content -LiteralPath ($configFile + '.tmp') -Encoding UTF8
    Move-Item -LiteralPath ($configFile + '.tmp') -Destination $configFile -Force
    Copy-Item -LiteralPath $PSCommandPath -Destination $installedScript -Force
    Set-PlayerShortcut ([Environment]::GetFolderPath('Desktop')) 'Pub Karaoke TV' $false
    Set-PlayerShortcut ([Environment]::GetFolderPath('Startup')) 'Pub Karaoke TV' $true
    Write-Host 'Select the wired mixer output in Windows Sound. Use its Test button to check the speakers, then close Sound.'
    Start-Process control.exe -ArgumentList 'mmsys.cpl,,0'
    $null = Read-Host 'Press Enter to open karaoke on the TV'
    Start-Process powershell.exe -WindowStyle Hidden -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File "' + $installedScript + '"')
    return
}

$guard = [Threading.Mutex]::new($false,'Local\PubKaraokeTVPlayer')
try { $owns = $guard.WaitOne(0) } catch [Threading.AbandonedMutexException] { $owns = $true }
if (-not $owns) { $guard.Dispose(); return }
$link = $null
$browser = $null
try {
    $cfg = Get-Content -Raw -LiteralPath $configFile | ConvertFrom-Json
    $options = Get-LinkOptions $cfg
    $probe = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback,0)
    $probe.Start(); $localPort = $probe.LocalEndpoint.Port; $probe.Stop()
    $local = "http://127.0.0.1:$localPort"
    Add-Type -AssemblyName System.Windows.Forms
    $monitor = [Windows.Forms.Screen]::AllScreens | Where-Object DeviceName -eq $cfg.screen | Select-Object -First 1
    if (-not $monitor) { $monitor = [Windows.Forms.Screen]::PrimaryScreen }
    $xy = '{0},{1}' -f $monitor.Bounds.X,$monitor.Bounds.Y
    $targets = @(@($cfg.host,$cfg.address) | Where-Object { $_ -and $_ -ne '127.0.0.1' } | Select-Object -Unique)
    $attempt = 0
    while ($true) {
        if (-not $link -or $link.HasExited) {
            $address = $targets[$attempt % $targets.Count]; $attempt++
            $argsSsh = $options + @('-N','-o','ExitOnForwardFailure=yes','-L',("127.0.0.1:${localPort}:127.0.0.1:" + $cfg.tv_port),"tv@$address")
            $link = Start-Process -FilePath $ssh -ArgumentList $argsSsh -WindowStyle Hidden -PassThru -RedirectStandardError (Join-Path $playerDir 'link.log')
        }
        if (-not $browser -or $browser.HasExited) {
            try { $health = Invoke-RestMethod "$local/api/health" -TimeoutSec 3 } catch { $health = $null }
            if ($health.ok -and $health.player_mode -eq 'laptop' -and -not $link.HasExited) {
                $browser = Start-Process $edge -ArgumentList @('--kiosk','--edge-kiosk-type=fullscreen','--no-first-run',
                    '--autoplay-policy=no-user-gesture-required',('--user-data-dir="' + (Join-Path $playerDir 'Edge') + '"'),
                    "--window-position=$xy","$local/tv?lite=1") -PassThru
            }
        }
        Start-Sleep -Seconds 2
    }
} finally {
    if ($link -and -not $link.HasExited) { $link.Kill() }
    if ($browser -and -not $browser.HasExited) { $browser.CloseMainWindow() | Out-Null }
    $guard.ReleaseMutex(); $guard.Dispose()
}
