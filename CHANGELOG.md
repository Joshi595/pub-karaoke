# Changelog

What changed for venues in each release. Updating keeps your `settings.json`, songs, logos and backups.

## 1.2.0 (2026-11-27)

**Safer nights**
- A guest's wish for a song whose artist and title have no Latin letters (Russian, Japanese, …) could delete the whole song library while it was being made. Such songs now get a safe folder name of their own.
- A `settings.json` that can't be read (a typo in Notepad, a power cut) no longer stops the app: it is kept aside and the newest backup is used. Values of the wrong kind fall back to their defaults with a warning; a blank PIN never opens the staff page.
- Saved files are flushed to disk before they replace the old ones, and the TV no longer rewrites the queue file every second.
- When a guest picks an unmade song while the laptop is making one in the background, the TV and the phones no longer freeze for up to half a minute.
- The internet link restarts after any error; a taken TV-link port no longer stops the app.
- Song maker: a full graphics card stops the batch instead of failing every song after it, a passing network problem no longer marks a song "video only", and a cover that won't download keeps the song.

**Staff**
- After one correct PIN, a staff phone stays unlocked for the night without keeping the PIN. Someone guessing PINs through the TV's QR address can no longer lock out staff who are already in.
- "Saved." after every change; the queue no longer redraws under your finger; removing a special night takes two taps; an unreadable accent colour is refused with a warning. Fixed the page scrolling sideways on phones.

**Guests**
- The search box and other fields are clearly outlined in every look; "Loading songs…" while the list arrives; no more double-added songs; Remove takes two taps.
- The phone buzzes and the tab title changes when it's your turn; screen readers announce it once. Polling pauses while the phone is locked.
- Clearer messages, a Copy button for the recovery code, and fixes for older iPhones.
- One phone can hold songs for three people, but can no longer fill the queue alone.

**TV and table cards**
- A song that won't play says so to the singer instead of silently calling the next name.
- The Wi-Fi QR code works for open networks; German possessives read "Hans' Song"; a tidier lobby.

**Checks**
- Every push runs a Python linter, a JavaScript syntax check, a PowerShell analyzer and axe-core accessibility checks of every page. Every look is tested for readable contrast.
- Releases are built only from tested tags on `main`, with `SHA256SUMS.txt` and signed build provenance: `gh attestation verify Setup-Pub-PC.bat -R Joshi595/pub-karaoke`.

## 1.1.0 (2026-11-26)

- The TV can be a laptop at the TV, linked to the pub PC: `Setup-Pub-PC.bat` on the PC, then the file it makes on the laptop.
- A separate guest listener, server-issued guest tickets with a private recovery code, daily backups and autostart on the pub PC.
- Tonight's theme, the Halloween look, logos per look, special nights and *Start again*.

## 1.0.0 (2026-10-30)

First public release: guests pick songs on their phones, songs are made on demand with lyrics timed to the singing, five looks, English and German.
