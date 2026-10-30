# Security

## Reporting a problem

Please report security problems privately, through
[GitHub's private vulnerability reporting](https://github.com/Joshi595/pub-karaoke/security/advisories/new),
not in a public issue. Say what an attacker could do, and how to reproduce it. You'll get an answer within a week.
Fixes go into the latest version on `main`; older versions aren't patched.

## What Pub Karaoke protects, and how

Pub Karaoke runs on one laptop at a venue. Guests' phones reach it over the venue's Wi-Fi or, with the internet
link on, over a Cloudflare quick tunnel.

- **Staff page:** every staff action needs the staff PIN. Setup creates a random 6-digit PIN.
  - Five wrong PINs lock that device out for a minute.
  - More than 30 wrong PINs over the internet in 10 minutes close the staff page to the internet for everyone, for up to 10 minutes. Staff on the laptop or the venue's own Wi-Fi can still get in.
  - The default PIN `1234` is refused over the internet.
- **The TV:** only the laptop itself can start and finish songs. Those requests must come from the laptop's own address, carry JSON (which other websites can't send without asking), and name the laptop by address. That last check blocks DNS rebinding. Requests that arrive through the tunnel never count as the laptop.
- **Guests:**
  - Guests can only remove their own songs.
  - Names lose control and invisible characters.
  - The queue holds at most 60 songs.
  - Song wishes can't carry commands to the song maker.
- **Pages:** a strict Content Security Policy lets the pages run only their own scripts (and YouTube's player on the TV), and no other site may put them in a frame. Guests' text is always inserted as text, never as HTML.
- **Secrets:** `settings.json` (PIN, Wi-Fi password) is never committed: it's in `.gitignore`. The Wi-Fi password is only sent to devices on the venue's own network, never over the internet link.
- **Song maker:** no shell command is ever built from a guest's text. yt-dlp is called through its Python API with a search prefix, so a wish can't turn into a command-line option. Song folders get names from a fixed alphabet (`a-z`, `0-9`, `-`), so a wish can't point outside `library/`.
  - It does fetch other code at run time: the vocal-removal models (on first use), and YouTube's player JavaScript, which yt-dlp runs under Node.js.

## Known limits

- On the venue's Wi-Fi the pages use plain `http://`, so someone listening on an open Wi-Fi can read the staff PIN when staff type it. Use a Wi-Fi with a password, or the internet link (`https://`), for the staff page.
- Over the internet link, every guest on the venue's Wi-Fi shares one public address. Five wrong PINs from one prankster lock that address out for a minute, staff included; staff can use the laptop meanwhile.
- The staff page runs on the laptop's port (5000). Keep the laptop's firewall rule limited to private networks (see the README).

## How the code is checked

Every push is checked by:

- **Tests:** on Windows, macOS and Linux.
- **Bandit:** Python security lint.
- **pip-audit:** known vulnerabilities in the pinned packages.
- **gitleaks:** secrets in the history.
- **OWASP ZAP:** a baseline scan of the running app.
- **CodeQL:** code scanning.
- **OpenSSF Scorecard:** how the repository itself is set up.

Dependabot proposes updates every week.
