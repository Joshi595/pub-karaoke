# Run karaoke without bringing a laptop

The dedicated pub PC is the server, song maker and TV player. Guests and staff use their phones. No paid hosting,
domain or cloud GPU is required. Hardware, power and the pub's existing internet connection are separate costs.

The free Cloudflare Quick Tunnel is an internet bridge to this PC. It has **no uptime guarantee**, and its address
changes whenever the tunnel is recreated. It is a best-effort option, rather than managed production hosting.
See [Cloudflare's limitations](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).

## Move to the pub PC

1. Use a supported Windows 11 PC or Linux desktop, an SSD, wired networking where available, HDMI to the TV and a
   wired audio connection to the mixer. Start with at least 16 GB RAM; allow more for CPU song preparation.
   A low-power mini PC can play prepared songs, but may prepare new songs slowly. Benchmark before buying hardware
   for fast live requests. A GPU is optional; there is no promised preparation time.
2. Finish the current event and close the old server. Keep the laptop installation as a fallback.
3. Run `.venv\Scripts\python run_karaoke.py --backup --library` on the old machine. This saves seven rotating private
   metadata snapshots and one incremental song-library copy in `backups/`. Keep a copy on another disk too: a backup
   on the same SSD does not protect against disk failure.
4. Copy the application, `library/`, `settings.json`, `history.json`, `catalog-status.json`, `starter-songs.txt`,
   `wishes.txt`, `needs-attention.txt`, `logo-*` and `backups/` to the new machine. Copy `guests.json` and `state.json`
   together if keeping current ticket credentials. Do not copy virtual environments; run setup again.
5. Run `setup.bat` (Windows) or `./setup.sh` (Linux). Install the song maker when asked. The app now needs the
   additional `tzdata` dependency on Windows; rerunning setup installs it. Startup replaces a default staff PIN
   automatically after backing up the previous settings. Read the PIN locally in `settings.json`.
6. Start with `start-karaoke.bat` or `./start.sh`. Wait for the local TV and internet QR code. The TV/browser and
   server each have a supervisor. Repeated Windows launches reuse healthy processes and the dedicated TV profile.

The ownership upgrade should be deployed **between events**. Tickets created by older versions using a client-chosen
device ID cannot be claimed by the new guest credentials. Finish or reset the old queue; the library and history stay.

## Addresses and firewall

| Address | Purpose |
|---|---|
| `http://localhost:5000/tv` | Local TV and audio; listener binds only to `127.0.0.1`. |
| `http://localhost:5000/print` | Print current joining cards and the Wi-Fi QR locally. |
| `http://PUB-PC-IP:5001/` | Guest access over the pub Wi-Fi, when device communication is allowed. |
| TV's current `https://…trycloudflare.com/` | Guests over Wi-Fi/mobile data; append `/admin` for staff. |

Allow incoming TCP **5001 only on the private venue network** if using local guest access. Do not open ports in the
internet router. Keep port 5000 private; the app does not expose it to the LAN. The tunnel connects to **5001** and
cannot return Wi-Fi passwords, serve library files, print private cards or call playback endpoints. HTTP headers
cannot override this listener boundary. Use the HTTPS tunnel or the PC itself for entering the staff PIN.

`port` and `guest_port` can be changed in `settings.json` and must differ. A custom reverse proxy must target the
guest port, never the local TV port. Running `flask run` or exposing `create_app()` directly bypasses the deployment
boundary; use `app.py` / `run_karaoke.py` as documented.

Prepared music stays on the pub PC and plays locally. When internet drops, current and prepared songs continue;
phones on the LAN can use the local guest address where Wi-Fi isolation allows it. New downloads and YouTube need
internet. If the public URL changes, guests rescan the TV, and staff sign in again. Guests can restore their own
tickets with the private code under **Keep or recover your songs**. Codes expire after 30 days; never share one.
Printed internet QR codes are temporary: reprint after a tunnel change.

## Start automatically

**Windows:** on the pub PC, sign in as its dedicated, non-administrator karaoke account. Open an elevated PowerShell
for that same account and run `powershell -ExecutionPolicy Bypass -File .\install-autostart.ps1`. This registers a
server task at boot using S4U and a separate TV task at interactive login. No password is saved by this installer.
The account needs access to this folder and permission to run scheduled tasks. S4U cannot use encrypted files or
network-share credentials: keep the application and songs on a local, unencrypted-by-EFS drive.

The screen needs a signed-in desktop. Arrange the pub's kiosk sign-in according to its Windows account policy;
the installer does not change login/security policy. In Task Scheduler, the tasks are **Pub Karaoke server** and
**Pub Karaoke TV**. Stop/disable them before updates or a restore. Reboot once and check both tasks.

**Linux desktop:** run `bash ./install-autostart.sh` as the karaoke account. Enable startup before login with
`sudo loginctl enable-linger YOUR_KARAOKE_USER`. The user systemd service runs the server; the desktop autostart
entry starts the TV after sign-in. Stop with `systemctl --user stop pub-karaoke.service`; disable with
`systemctl --user disable pub-karaoke.service`. Remove `~/.config/autostart/pub-karaoke.desktop` to stop TV autostart.
The installer targets systemd Linux; macOS can continue using `./start.sh` manually.

Disable sleep while plugged in, schedule OS updates outside event hours, and enable power-on-after-power-loss in
the BIOS if supported. These hardware/account settings must be checked on the actual pub PC.

## Staff operation and monitoring

- Staff can close/reopen requests without interrupting the current queue. **Start a fresh night** clears queued
  singers and fairness counts, and requires a second tap. It is disabled while someone is singing.
- At **6 am Europe/Berlin**, session state rolls over automatically on the next API request. If a song is playing,
  rollover waits until it finishes. Venue settings, the library and popularity history remain.
- **System status** shows the internet/local addresses, free disk space, song-maker availability, last worker
  failure and last successful backup. The server restarts after a crash or repeated failed health checks.
- Supervisor/server output rotates in `logs/supervisor.log` (up to four 2 MB files). Worker diagnostics are in
  `work/maker.log`. Both logs can contain song titles and singer names; treat backups and logs as private.
- Default worker deadline: **3600 seconds**, with at most two attempts for transient failures. Configure
  `maker_timeout_seconds` (30–14400) in settings or the staff settings API. Long CPU processing may need a larger
  deadline; staff see actual stages, not a GPU-based countdown.
- `library_max_gb` defaults to **20 GB**; `min_free_gb` defaults to **5 GB**. Both requested and background downloads
  must respect them. Already prepared songs remain playable. New recordings longer than ten minutes are rejected.
- Guest submissions are limited to 5/minute per guest and 60/minute per source IP. External lookups have two slots
  and cache results. Guest credential creation allows 240/hour per source IP. Shared pub Wi-Fi guests share an IP.
- One song-maker process owns an OS lock. Do not schedule another nightly maker while the live maker is running.
  The live maker already prepares songs while idle. Abandoned scratch folders older than a day are cleaned on
  worker startup; incomplete/replaced originals are retained under `work/` for inspection.

## Backup and restore

Daily automatic backups keep seven private metadata ZIPs and an incremental copy in `backups/library/`. Audio is
copied only when changed. Old deleted songs in the mirror remain available for recovery. Allow disk space for
both the live library and its backup. A failed library copy is reported and retried; it is not marked successful.

Manual backup: `.venv\Scripts\python run_karaoke.py --backup --library`.

To restore, stop **both scheduled tasks**, close the TV/server, then run:

```
.venv\Scripts\python run_karaoke.py --restore backups\YOUR-SNAPSHOT.zip --library
```

On Linux/macOS substitute `.venv/bin/python`. The command refuses to overwrite a running server and creates a
metadata snapshot before restoring. ZIPs contain settings/queue/history/guest credentials/logos; the song mirror
is the most recently backed-up library, not a historical library for every ZIP. Restore uses safe, known paths.

## Acceptance rehearsal on the pub equipment

The automated checks use synthetic audio and mocked external services. They cannot establish real TV latency,
sound-device quality, YouTube availability at this venue or AI throughput on a different PC.

1. Reboot and verify automatic startup, sound output, staff login over HTTPS and scanning from mobile data.
2. Run the TV sync test, adjust screen delay, and sing a complete prepared song through the actual mixer.
3. Request a not-yet-made song. Record its start/finish time from the staff status/server log and note CPU/GPU
   hardware. Test several songs before advertising a preparation time. Confirm playback stays smooth meanwhile.
4. Run a **four-hour rehearsal** with several rounds and multiple phones. Test skip, pause, restart, closing requests,
   cancellation and a fresh-night reset. Check memory, free space and backup status at the start and finish.
5. Disconnect internet during a prepared song. It must finish normally; test LAN joining and later reconnection.
6. End/restart the tunnel, rescan its new QR and recover one guest's tickets with the private recovery code.
7. End the server process and close the kiosk browser separately. Each supervisor must recover its own process.
   Check that an old completion request never skips the next singer.
8. Test unavailable YouTube playback, a backup/restore on a spare copy, and a simulated next-day rollover outside
   an active event. Keep the laptop fallback until this rehearsal passes.

Run automated tests with `python -m pytest -q --ignore=test_browser.py`. For browser checks install
`requirements-test.txt`, run `python -m playwright install chromium`, then `python -m pytest -q test_browser.py`.
