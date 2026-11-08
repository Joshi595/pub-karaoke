# Security

## Reporting a problem

Please report security problems privately, through
[GitHub's private vulnerability reporting](https://github.com/Joshi595/pub-karaoke/security/advisories/new),
not in a public issue. Say what an attacker could do, and how to reproduce it. You'll get an answer within a week.
Fixes go into the latest version on `main`; older versions aren't patched.

## What Pub Karaoke protects, and how

Pub Karaoke runs on one laptop at a venue. Guests' phones reach it over the venue's Wi-Fi or, with the internet
link on, over a Cloudflare quick tunnel.

Use `app.py` or `run_karaoke.py` to start the server. The deployment has two listeners: **127.0.0.1:5000** for the
local TV and private data, and **port 5001** for public/LAN guest and staff traffic. The tunnel targets 5001. The
public WSGI boundary is server-owned and cannot be changed by proxy headers. It blocks TV controls, library
downloads and private print pages, and always removes the Wi-Fi password. A reverse proxy must never target 5000.

- **Staff page:** every staff action needs the staff PIN. Setup creates a random 6-digit PIN.
  - Startup backs up and replaces an existing default PIN. The replacement is read locally from `settings.json`.
  - Five wrong PINs lock that device out for a minute.
  - More than 30 wrong PINs over the internet in 10 minutes close the staff page to the internet for everyone, for up to 10 minutes. Staff on the laptop or the venue's own Wi-Fi can still get in.
  - The default PIN `1234` is refused over the internet.
- **The TV:** only the laptop itself can start and finish songs. Those requests must come from the laptop's own address, carry JSON (which other websites can't send without asking), and name the laptop by address. That last check blocks DNS rebinding. Requests that arrive through the tunnel never count as the laptop.
- **Guests:**
  - Public queue changes require a cryptographically random server-issued guest token. Only its SHA-256 digest is
    stored in `guests.json`. The token is also the private recovery code for a new tunnel hostname; it expires
    after 30 days. It is not included in public queue state or URLs.
  - Tokens identify a browser, not a verified person. Submission/IP limits bound abuse; clearing browser storage
    can still create a new identity. Name-based singer fairness is not identity verification.
  - Expensive lookups have bounded concurrency and caching. Submission and credential recovery endpoints are rate-limited.
  - Guests can only remove their own songs.
  - Names lose control and invisible characters.
  - The queue holds at most 60 songs.
  - Song wishes can't carry commands to the song maker.
- **Pages:** a strict Content Security Policy lets the pages run only their own scripts (and YouTube's player on the TV), and no other site may put them in a frame. Guests' text is always inserted as text, never as HTML.
- **Secrets:** `settings.json` (PIN, Wi-Fi password) is never committed: it's in `.gitignore`. The Wi-Fi password is only sent through the local TV listener, never through the guest listener or internet link.
- **Song maker:** no shell command is ever built from a guest's text. yt-dlp is called through its Python API with a search prefix, so a wish can't turn into a command-line option. Song folders get names from a fixed alphabet (`a-z`, `0-9`, `-`), so a wish can't point outside `library/`.
  - It does fetch other code at run time: the vocal-removal models (on first use), and YouTube's player JavaScript, which yt-dlp runs under Node.js.

## Known limits

- On the venue's Wi-Fi the pages use plain `http://`, so someone listening on an open Wi-Fi can read the staff PIN when staff type it. Use a Wi-Fi with a password, or the internet link (`https://`), for the staff page.
- Over the internet link, every guest on the venue's Wi-Fi shares one public address. Five wrong PINs from one prankster lock that address out for a minute, staff included; staff can use the laptop meanwhile.
- Guest/staff phones now use 5001. Local 5000 is loopback-only. Keep LAN 5001 limited to private networks.
- The free internet tunnel has no availability guarantee and changes hostname on recreation. Prepared audio stays
  local. Guests must rescan after an address change and can recover tickets using their private recovery code.
- Backups contain secrets (including older PINs); logs can contain names/song requests. They are ignored by git
  and must be kept private. Local backups do not protect against loss of the whole disk.

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
