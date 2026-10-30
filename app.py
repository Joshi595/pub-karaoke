"""Pub Karaoke live app: guest phones, staff phone and the TV, all on the venue's laptop."""
import hmac
import ipaddress
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import threading
import time
import unicodedata
import uuid
from functools import wraps
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, abort, jsonify, request, send_from_directory

from catalog import Catalog
from make_songs import KARAFUN_LIST, has_synced_lyrics, library_gb

NEW_NIGHT_AFTER = 12 * 3600
MAX_QUEUE = 60  # the whole queue: anonymous phones can't flood it with made-up names
MAKER_PY = Path(".venv-maker", "Scripts", "python.exe") if os.name == "nt" else Path(".venv-maker", "bin", "python")


class QueueError(Exception):
    """args[0] is the error code shown to the phone: limit, duplicate, unknown_song, bad_name, forbidden, not_found."""


def write_json(path, data, indent=None):
    """Write via a temp file so a crash never leaves half a file behind."""
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")
    for attempt in range(5):  # antivirus or the indexer can hold the file for a moment on Windows
        try:
            tmp.replace(path)
            return True
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    return False


def clean_name(s):
    # no control or invisible characters (right-to-left overrides, zero-width spaces): names must read as they show
    s = "".join(c for c in str(s or "") if unicodedata.category(c) not in ("Cc", "Cf")).strip()[:24]
    if not s:
        raise QueueError("bad_name")
    return s


class Party:
    """Tonight's queue. Fair order: whoever has sung least goes next; staff can pin one song to the front."""

    def __init__(self, songs, songs_per_singer=2, path=None, now=time.time, max_wait=90, can_make=False):
        self.songs, self.songs_per_singer, self.path, self.now = songs, songs_per_singer, path, now
        self.queue, self.turns = [], {}
        self.now_playing, self.paused, self.volume, self.help_vocals = None, False, 1.0, None
        self.nudge, self.synctest = 0.0, False  # nudge: seconds the current song's lyrics are moved earlier
        # can_make: this laptop has the song maker, so wished songs are waited for. Without it, a wish plays as a
        # karaoke video max_wait seconds after it was picked.
        self.max_wait, self.can_make = max_wait, can_make

    def add(self, name, device, song_id, wish=None, yt=(), catalog=None, video=False):
        """A wish is a song not in the library yet: it plays from the library once made, else from YouTube (yt ids).
        catalog: its id in the song list. video: it can't be made (no timed lyrics), so it plays from YouTube."""
        if not wish and (not isinstance(song_id, str) or song_id not in self.songs):
            raise QueueError("unknown_song")
        name = self.check(name, song_id, wish)
        entry = {"id": uuid.uuid4().hex[:8], "name": name, "device": str(device)[:64], "song_id": song_id,
                 "at": self.now(), "pinned": False}
        if wish:
            entry.update(wish=wish, yt=list(yt))
        if catalog:
            entry["catalog"] = catalog
        if video:
            entry["video"] = True
        self.queue.append(entry)
        self.save()
        return entry

    def check(self, name, song_id, wish=None):
        """Would this pick be accepted? Raises like add(), so phones hear 'no' before any slow lookup."""
        name = clean_name(name)
        if len(self.queue) >= MAX_QUEUE:
            raise QueueError("full")
        mine = [e for e in self.queue if e["name"].lower() == name.lower()]
        # the same song twice: same library song, or same wish (a made wish keeps both)
        if any((song_id and e["song_id"] == song_id) or (wish and e.get("wish") == wish) for e in mine):
            raise QueueError("duplicate")
        if len(mine) >= self.songs_per_singer:
            raise QueueError("limit")
        return name

    def _find(self, entry_id):
        for e in self.queue:
            if e["id"] == entry_id:
                return e
        raise QueueError("not_found")

    def remove(self, entry_id, device=None, staff=False):
        e = self._find(entry_id)
        if not staff and e["device"] != device:
            raise QueueError("forbidden")
        self.queue.remove(e)
        self.save()

    def pin(self, entry_id):
        self._find(entry_id)["pinned"] = True
        self.save()

    def upcoming(self):
        left, picks, order = list(self.queue), {}, []
        while left:
            k = lambda e: (not e["pinned"], self.turns.get(e["name"].lower(), 0) + picks.get(e["name"].lower(), 0), e["at"])
            e = min(left, key=k)
            left.remove(e)
            picks[e["name"].lower()] = picks.get(e["name"].lower(), 0) + 1
            order.append(e)
        return order

    def ready(self, e):
        return e["song_id"] in self.songs or bool(e.get("video") and e.get("yt"))

    def next(self):
        """The first singer in fair order whose song is ready. Anyone still waiting for theirs keeps their place,
        because turns only count once sung. A song being made is waited for; YouTube only plays songs that can't be
        made (or, with no song maker on this laptop, a wish max_wait seconds after it was picked)."""
        if self.now_playing:
            return self.now_playing
        # a song deleted from the library that nobody is making can never play
        self.queue = [e for e in self.queue if e["song_id"] in self.songs or e.get("wish")]
        up = self.upcoming()
        pick = next((e for e in up if self.ready(e)), None)
        if pick is None and not self.can_make:
            pick = next((e for e in up if e.get("yt") and self.now() - e["at"] >= self.max_wait), None)
        if pick:
            self.queue.remove(pick)
            key = pick["name"].lower()
            self.turns[key] = self.turns.get(key, 0) + 1
            self.now_playing = pick
            song = self.songs.get(pick["song_id"], {})
            self.help_vocals = song.get("help_vocals", 0.25)
            self.nudge = song.get("sync", {}).get("nudge", 0.0)
        self.save()
        return self.now_playing

    def made(self, wish, slug):
        """The song maker finished a wish: queued entries waiting for it now play the real song."""
        for e in self.queue:
            if e.get("wish") == wish and not e["song_id"]:
                e["song_id"] = slug
        self.save()

    def unmakeable(self, wish):
        """The maker gave up on a wish: entries for it play the YouTube video now, or leave if there's none."""
        waiting = lambda e: e.get("wish") == wish and not e["song_id"]
        self.queue = [e for e in self.queue if not (waiting(e) and not e.get("yt"))]
        for e in self.queue:
            if waiting(e):
                e["video"] = True
        self.save()

    def done(self, entry_id):
        if not self.now_playing or self.now_playing["id"] != entry_id:
            return False
        self.now_playing = None
        self.save()
        return True

    SAVED = ("queue", "turns", "now_playing", "paused", "volume", "help_vocals", "nudge")

    def save(self):
        if self.path and not write_json(self.path, {**{k: getattr(self, k) for k in self.SAVED}, "saved_at": self.now()}):
            print("warning: could not save state.json; the queue is still in memory")

    @classmethod
    def load(cls, path, songs, songs_per_singer, now=time.time):
        p = cls(songs, songs_per_singer, path, now)
        try:
            state = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return p
        if now() - state.get("saved_at", 0) > NEW_NIGHT_AFTER:
            return p
        for k in cls.SAVED:
            setattr(p, k, state.get(k, getattr(p, k)))
        return p


# ---------------------------------------------------------------- web app

SHELVES = ("ready", "here", "top", "classics", "irish", "german", "schlager", "80s", "rock", "country", "duets")
LOOKS = ("stage", "pub", "neon", "daylight")
DEFAULT_SETTINGS = {"pin": "1234", "songs_per_singer": 2, "upnext_seconds": 15, "wifi_name": "", "wifi_password": "",
                    "pub_name": "Karaoke Night", "port": 5000, "public_url": "", "max_wait_seconds": 90,
                    "hide_explicit": True, "languages": [], "auto_download": True, "library_max_gb": 20,
                    "internet_link": True, "look": "stage", "accent": "", "icon": "🎤",
                    "shelves": ["ready", "here", "top", "classics", "80s", "rock", "country", "duets"]}
TUNNEL_ADDRESS = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def tunnel_address(line):
    """The web address cloudflared prints once the internet link is up."""
    m = TUNNEL_ADDRESS.search(line)
    return m.group(0) if m else None


def tunnel_online(url, wait=60):
    """True once the internet knows the new address. Asked of Cloudflare's public lookup, never the pub's router:
    a router asked a moment too early remembers 'no such address' for many minutes, and phones on its Wi-Fi with it."""
    import urllib.parse
    import urllib.request
    host = urllib.parse.urlparse(url).hostname
    for _ in range(wait // 3):
        try:
            req = urllib.request.Request(f"https://cloudflare-dns.com/dns-query?name={host}&type=A", headers={"Accept": "application/dns-json"})
            with urllib.request.urlopen(req, timeout=5) as r:  # a fixed https:// address  # nosec B310
                if json.load(r).get("Answer"):
                    return True
        except (OSError, ValueError):
            pass
        time.sleep(3)
    return False
LIBRARY_FILES = {"instrumental.m4a", "vocals.m4a", "lyrics.json", "song.json", "cover.jpg"}
THEME_NAMES = ("celtic", "neon80s", "disco", "rock", "ballad", "pop", "cover")
DEFAULT_DISPLAY = {"layout": "auto", "highlight": "auto", "size": "L", "position": "middle", "next_line": True,
                   "dots": True, "band": False, "theme": "auto", "screen_delay_ms": 0}


def one_of(*options):
    return lambda v: v if isinstance(v, str) and v in options else None


def number(lo, hi, kind=float):
    def check(v):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        return kind(v) if lo <= v <= hi else None
    return check


def flag(v):
    return v if isinstance(v, bool) else None


def names(v):
    return v if isinstance(v, list) and len(v) < 40 and all(isinstance(x, str) and 0 < len(x) < 30 for x in v) else None


def words(max_len, banned=""):
    """A short line of printable text (no control or invisible characters), none of the banned ones."""
    def check(v):
        if not isinstance(v, str) or not v.isprintable() or any(c in banned for c in v):
            return None
        v = v.strip()
        return v if 0 < len(v) <= max_len else None
    return check


def colour(v):
    return v if isinstance(v, str) and re.fullmatch(r"(#[0-9a-fA-F]{6})?", v) else None  # "" = the look's own


def shelves(v):
    ok = isinstance(v, list) and all(isinstance(x, str) and x in SHELVES for x in v) and len(set(v)) == len(v)
    return v if ok else None


# What staff may change from the admin page, and what each value may be. Anything else (the PIN!) stays in Notepad.
EDITABLE = {
    "display": {"layout": one_of("auto", "classic", "scroll", "bigline", "ball"), "highlight": one_of("auto", "wipe", "glow", "pop"),
                "size": one_of("S", "M", "L", "XL"), "position": one_of("middle", "lower"), "next_line": flag, "dots": flag,
                "band": flag, "theme": one_of("auto", *THEME_NAMES), "screen_delay_ms": number(-1000, 1000, int)},
    "songs_per_singer": number(1, 5, int),
    "upnext_seconds": number(5, 60, int),
    "max_wait_seconds": number(0, 600, int),
    "hide_explicit": flag,
    "languages": names,  # song languages guests can find; empty = all
    "auto_download": flag,
    "library_max_gb": number(1, 2000, int),
    "pub_name": words(40),
    "look": one_of(*LOOKS),
    "accent": colour,
    "icon": words(8, "<>&\"'"),  # it also goes into the pages' SVG favicon
    "shelves": shelves,
}


def next_to_make(party, skip=()):
    """The song needed soonest that isn't made yet: the maker works in singing order, not request order."""
    for e in party.upcoming():
        if e.get("wish") and not party.ready(e) and not e.get("video") and e["wish"] not in skip:
            return e
    return None


def merge_settings(current, changes, rules=EDITABLE):
    """Staff changes checked key by key. One bad key refuses the lot, so nothing is half-applied."""
    if not isinstance(changes, dict):
        raise QueueError("bad_setting")
    out = dict(current)
    for k, v in changes.items():
        rule = rules.get(k)
        if isinstance(rule, dict):
            out[k] = merge_settings(current.get(k, {}), v, rule)
            continue
        checked = rule(v) if rule else None
        if checked is None:
            raise QueueError("bad_setting")
        out[k] = checked
    return out


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def lyric_lines(folder):
    return [line.get("text", "") for line in read_json(folder / "lyrics.json", [])]


def load_songs(library):
    songs = {}
    for f in sorted(library.glob("*/song.json")):
        try:
            songs[f.parent.name] = {**json.loads(f.read_text(encoding="utf-8")), "id": f.parent.name}
        except (OSError, ValueError):  # half-written, or held by the antivirus for a moment: picked up next time
            pass
    return songs


def karaoke_videos(text):
    """YouTube ids of karaoke versions of a song: the TV's fallback while (or if) the maker can't make it."""
    try:
        import yt_dlp
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "extract_flat": True, "socket_timeout": 10}) as y:
            found = y.extract_info(f"ytsearch10:{text} karaoke", download=False).get("entries") or []
    except Exception as e:  # no internet, YouTube changed: the maker may still make the song
        print(f"YouTube search failed for {text!r}: {e}", flush=True)
        return []
    return [v["id"] for v in found if v and "karaoke" in (v.get("title") or "").lower() and (v.get("duration") or 0) < 600][:5]


def local_host(host):
    """The TV is opened as localhost or by an IP address. Any other name is a website pointing its name at this
    laptop (DNS rebinding) to drive the queue from a browser here."""
    name = urlsplit("//" + host).hostname or ""
    try:
        ipaddress.ip_address(name)
        return True
    except ValueError:
        return name == "localhost"


def lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def bind_exclusive(port):
    """Listening socket nobody else can share. A second copy of the app (staff double-clicking the icon again)
    must fail loudly instead of silently splitting the queue between two servers on one port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        s.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    else:  # macOS/Linux: a restart may reuse the port at once; a second live copy is still refused
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(("0.0.0.0", port))  # phones on the Wi-Fi must reach the laptop  # nosec B104
        s.listen(128)
    except OSError:
        s.close()
        raise
    return s


def ensure_settings(root):
    """settings.json, written on first start (or by setup) with a random staff PIN, never one everybody knows."""
    f = Path(root) / "settings.json"
    if not f.exists():
        pin = f"{secrets.randbelow(10 ** 6):06d}"
        write_json(f, {**DEFAULT_SETTINGS, "pin": pin}, indent=1)
        print(f"Created settings.json. Staff PIN: {pin} (write it down; change it in settings.json)", flush=True)
    return f


def create_app(root):
    root = Path(root)
    settings = {**DEFAULT_SETTINGS, **json.loads(ensure_settings(root).read_text(encoding="utf-8-sig"))}
    library = root / "library"
    library.mkdir(exist_ok=True)
    songs = load_songs(library)
    party = Party.load(root / "state.json", songs, settings["songs_per_singer"])
    party.max_wait = settings["max_wait_seconds"]
    lock = threading.Lock()
    static = root / "static"
    app = Flask(__name__, static_folder=str(static), static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # every request is a few hundred bytes of JSON

    @app.after_request
    def security_headers(r):
        """The pages run only their own scripts (and YouTube's player on the TV), and no other site may frame them."""
        r.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' https://www.youtube.com; "
            "frame-src https://www.youtube.com https://www.youtube-nocookie.com; img-src 'self' data:; "
            "style-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; "
            "form-action 'self'; object-src 'none'")
        r.headers["X-Content-Type-Options"] = "nosniff"
        r.headers["Referrer-Policy"] = "no-referrer"
        r.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
        r.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        r.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        if request.path.startswith("/api/"):  # names in the queue, staff data: never kept by a cache on the way
            r.headers["Cache-Control"] = "no-store"
        return r

    csv_file, starter = library / "karafuncatalog.csv", root / "starter-songs.txt"
    catalog = Catalog(csv_file if csv_file.exists() else None, starter.read_text(encoding="utf-8") if starter.exists() else "")
    if not csv_file.exists():
        print(f"Guests can only find the starter list: for ~90,000 songs, save the CSV from {KARAFUN_LIST} as {csv_file}", flush=True)
    status_file, history_file = root / "catalog-status.json", root / "history.json"
    status = read_json(status_file, {})    # catalog id -> "no_lyrics" | "failed": only the YouTube karaoke video can play
    history = read_json(history_file, {})  # catalog id -> [times picked here, last picked]: "Popular here" and auto-download
    seen = [None]

    def refresh_library(force=False):
        """Songs made beside the app (its own maker, the nightly run) show up without a restart; deleted ones go."""
        found = {p.name for p in library.iterdir() if p.is_dir()}
        if force or found != seen[0]:
            seen[0] = found
            fresh = load_songs(library)
            songs.clear()
            songs.update(fresh)
            catalog.set_library(songs, {slug: lyric_lines(library / slug) for slug in songs})

    refresh_library()
    filters = lambda: {"hide_explicit": settings["hide_explicit"], "langs": settings["languages"] or None}
    popular = lambda: {cid: n for cid, (n, _) in history.items()}

    def info(e):
        if e["song_id"] in songs:
            return songs[e["song_id"]]
        return (e.get("catalog") and catalog.get(e["catalog"])) or {"artist": "", "title": e.get("wish", "")}

    # The song maker: one song at a time on this laptop (the vocal remover needs the whole graphics card).
    maker_py = root / MAKER_PY
    party.can_make = maker_py.exists()
    making, wake, proc = {}, threading.Event(), [None]  # making: wish, catalog, stage, pct
    failed = {}  # wish -> failed tries tonight; GIVE_UP or more: not tried again tonight
    retimes = []  # songs staff asked to time again
    GIVE_UP = 2
    gave_up = lambda: {w for w, n in failed.items() if n >= GIVE_UP}

    # The two long stages report only when they start; fill in by how long they usually take (RTX 3060, overlap 4)
    LONG_STAGES = {"separate": (25, 75, 150), "timing": (75, 95, 60)}  # stage: (from %, to %, usual seconds)

    def progress():
        pct = making.get("pct", 0)
        if making.get("stage") in LONG_STAGES:
            lo, hi, secs = LONG_STAGES[making["stage"]]
            pct = lo + (hi - lo) * min(0.95, (time.time() - making.get("since", time.time())) / secs)
        return int(pct)

    def entry_status(e):
        if e["song_id"] in songs:
            return "ready"
        if e.get("video"):
            return "video"
        return "making" if making.get("wish") == e.get("wish") else "waiting"

    def view(e, device=None):
        song, st = info(e), entry_status(e)
        out = {"id": e["id"], "name": e["name"], "song_id": e["song_id"], "pinned": e["pinned"], "status": st,
               "mine": bool(device) and e["device"] == device,
               "song": {"artist": song.get("artist", ""), "title": song.get("title", "")}}
        if st == "making":
            out["pct"] = progress()
        return out

    def playing(device=None):
        np = party.now_playing
        return {**info(np), **view(np, device), "yt": np.get("yt", [])} if np else None

    def mark(v):
        """Search results: say which songs can only play as a YouTube video, and which one is being made now."""
        if v["status"] == "make":
            if status.get(v["id"]):
                v["status"] = "video"
            elif making.get("catalog") == v["id"]:
                v["status"] = "making"
        return v

    def run_job(text):
        """Hand one song to the song maker, started once so its AI models stay loaded. Returns (folder, why not)."""
        p = proc[0]
        if p is None or p.poll() is not None:
            (root / "work").mkdir(exist_ok=True)
            log = open(root / "work" / "maker.log", "a", encoding="utf-8")
            # overlap 4: ~2.5 min per song on an RTX 3060 instead of ~3.5 at the overnight default of 8, slightly more vocal bleed
            p = proc[0] = subprocess.Popen([str(maker_py), "-X", "utf8", "-u", "make_songs.py", "--serve", "--overlap=4"], cwd=root,
                                           stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=log, text=True, encoding="utf-8", errors="replace")
        p.stdin.write(text + "\n")
        p.stdin.flush()
        for line in p.stdout:
            kind, _, rest = line.strip().partition(" ")
            if kind == "STAGE":
                stage, _, pct = rest.partition(" ")
                with lock:
                    making.update(stage=stage, pct=int(pct) if pct.isdigit() else 0, since=time.time())
            elif kind in ("SLUG", "FAIL"):
                return (rest, "") if kind == "SLUG" else (None, rest)
        return None, "the song maker stopped"

    def next_job():
        """Guests' songs first (in singing order), then songs staff want re-timed, then this pub's favourites."""
        given_up = gave_up()
        e = next_to_make(party, given_up)
        if e:
            return {"wish": e["wish"], "catalog": e.get("catalog")}
        if retimes:
            slug = retimes.pop(0)
            return {"wish": f"RETIME {slug}", "catalog": None, "retime": slug}
        if not settings["auto_download"] or library_gb(library) >= settings["library_max_gb"]:
            return None
        # idle: this pub's favourites, made before anyone asks
        skip = set(status) | {cid for cid, w in prefetched.items() if w in given_up}
        row = catalog.prefetch(popular(), skip=skip, **filters())
        if not row:
            return None
        wish = f"{row['artist']} - {row['title']}"
        prefetched[row["id"]] = wish
        return {"wish": wish, "catalog": row["id"], "prefetch": True}

    prefetched = {}  # catalog id -> wish text, for idle-time songs

    def hurry():
        """A guest is waiting for a song: stop an idle-time song half-way (it's made again later) so theirs starts
        now instead of up to 3 minutes later."""
        p = proc[0]
        if making.get("prefetch") and p and p.poll() is None:
            making["interrupted"] = True
            # the venv's python.exe is a launcher with the real interpreter as its child: end both
            subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True) if os.name == "nt" else p.kill()

    def maker_loop():
        while True:
            try:
                make_next()
            except Exception as err:  # one bad song or locked file must not stop the song maker for the night
                print(f"Song maker problem: {type(err).__name__}: {err}", flush=True)
                with lock:
                    making.clear()
                time.sleep(10)

    def make_next():
        with lock:
            job = next_job()
            if job:
                making.clear()
                making.update(job, stage="starting", pct=0)
        if not job:
            wake.wait(30)
            wake.clear()
            return
        print(f"Making: {job['wish']}", flush=True)
        try:
            slug, why = run_job(job["wish"])
        except OSError as err:  # the maker process died between songs
            slug, why = None, f"error {err}"
        wish = job["wish"]
        with lock:
            interrupted = making.get("interrupted")
            making.clear()
            refresh_library(force=True)
            if interrupted:
                return print(f"Paused {wish!r}: a guest's song goes first", flush=True)
            if job.get("retime"):
                return print(f"Re-timed: {job['retime']}" if slug else f"Couldn't re-time {job['retime']}: {why}", flush=True)
            if slug in songs:
                party.made(wish, slug)
                return print(f"Ready: {slug}", flush=True)
            # no lyrics or no recording won't change tonight; a crash or a network blip might: one more try
            lasting = not why.startswith("error") and why != "the song maker stopped"
            failed[wish] = GIVE_UP if lasting else failed.get(wish, 0) + 1
            print(f"Couldn't make {wish!r}: {why}", flush=True)
            if failed[wish] < GIVE_UP:
                return
            no_video = any(e.get("wish") == wish and not e["song_id"] and not e.get("yt") for e in party.queue)
        yt = karaoke_videos(wish) if no_video else []  # the fallback search may not have finished yet: don't drop anyone early
        with lock:
            for e in party.queue:
                if e.get("wish") == wish and not e.get("yt"):
                    e["yt"] = yt
            party.unmakeable(wish)
            if job["catalog"] and lasting:
                status[job["catalog"]] = "failed"
                write_json(status_file, status)

    if maker_py.exists():
        threading.Thread(target=maker_loop, daemon=True).start()

    def remember_pick(cid):
        if cid:
            history[cid] = [history.get(cid, [0, 0])[0] + 1, int(time.time())]
            write_json(history_file, history)

    def find_videos(text):
        """The YouTube karaoke fallback for a song being made, looked up after the guest has their answer."""
        yt = karaoke_videos(text)
        with lock:
            for e in party.queue:
                if e.get("wish") == text and not e.get("yt"):
                    e["yt"] = yt
            party.save()

    # The internet link: many venue Wi-Fis keep phones from reaching the laptop, so phones come in over the internet
    # instead, through a free Cloudflare tunnel (cloudflared, installed by setup or put in tools/). Its address is new
    # each time it starts; the TV's QR code follows it.
    tunnel = [None]
    tunnel_exe = Path(shutil.which("cloudflared") or root / "tools" / "cloudflared.exe")

    def run_tunnel():
        while True:
            try:
                p = subprocess.Popen([str(tunnel_exe), "tunnel", "--no-autoupdate", "--url", f"http://localhost:{settings['port']}"],
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")
                for line in p.stdout:
                    url = tunnel_address(line)
                    if url and url != tunnel[0]:
                        tunnel_online(url)  # the QR code shows it only once phones can find it
                        time.sleep(5)  # a little longer, for Cloudflare's own servers to catch up
                        tunnel[0] = url
                        print(f"Guests over the internet: {url}/", flush=True)
            except OSError as err:
                print(f"Internet link problem: {err}", flush=True)
            tunnel[0] = None
            print("Internet link dropped; trying again in 10 s. Phones on the pub's own network still work.", flush=True)
            time.sleep(10)

    def start_tunnel():  # called once the server has its port, so a refused second copy leaves no stray tunnel
        if settings["internet_link"] and tunnel_exe.exists():
            threading.Thread(target=run_tunnel, daemon=True).start()

    app.config["start_tunnel"] = start_tunnel
    join_url = lambda: settings["public_url"] or (tunnel[0] and tunnel[0] + "/") or f"http://{lan_ip()}:{settings['port']}/"

    def body():
        return request.get_json(silent=True) or {}

    wrong_pins = {}  # device address -> (failures, locked_until)
    internet_fails = []  # when wrong PINs came in over the internet link, for the last 10 minutes

    # Over the internet link every request arrives from cloudflared on this laptop, and Cloudflare's header names the
    # phone. Only requests from this laptop may carry it: a phone on the Wi-Fi could fake it to dodge the lockout.
    # Requests over the internet are never the TV, however local they look.
    via_internet = lambda: request.remote_addr in ("127.0.0.1", "::1") and ("Cf-Connecting-Ip" in request.headers or "Cf-Ray" in request.headers)
    client_ip = lambda: (via_internet() and request.headers.get("Cf-Connecting-Ip")) or request.remote_addr

    def admin(fn):
        @wraps(fn)
        def wrapped(*a, **kw):
            with lock:  # the counts below are shared by 16 server threads
                who, now = client_ip(), time.time()
                fails, until = wrong_pins.get(who, (0, 0))
                internet_fails[:] = [t for t in internet_fails if now - t < 600]
                # many addresses guessing at once (one attacker can have thousands): the internet way in closes for
                # all for a while; staff on the laptop or the venue's own Wi-Fi aren't affected
                if now < until or (via_internet() and len(internet_fails) >= 30):
                    return jsonify(error="locked"), 429
                if via_internet() and str(settings["pin"]) == DEFAULT_SETTINGS["pin"]:
                    return jsonify(error="pin_too_easy"), 409  # the staff page is on the internet: 1234 won't do
                if not hmac.compare_digest(request.headers.get("X-Pin", "").encode(), str(settings["pin"]).encode()):
                    fails += 1  # five wrong guesses lock that device out for a minute
                    wrong_pins[who] = (0, now + 60) if fails >= 5 else (fails, 0)
                    if via_internet():
                        internet_fails.append(now)
                    return jsonify(error="forbidden"), 403
                wrong_pins.pop(who, None)
                return fn(*a, **kw)
        return wrapped

    laptop = {"127.0.0.1", "::1"}

    def from_laptop(addr):
        """The TV may be opened as localhost or by the address shown under the QR code: both are this laptop."""
        if addr not in laptop:  # the laptop's address can change (Wi-Fi, DHCP): look again before refusing
            laptop.add(lan_ip())
            try:
                laptop.update(socket.gethostbyname_ex(socket.gethostname())[2])
            except OSError:
                pass
        return addr in laptop

    def tv_only(fn):  # the TV runs on the laptop itself; a guest's phone must not drive the queue
        @wraps(fn)
        def wrapped(*a, **kw):
            # JSON only: a browser asks first before another website may send that, so no web page open on this
            # laptop can skip singers; and the TV is opened by address, never by a website's name
            if via_internet() or not from_laptop(request.remote_addr) or not request.is_json or not local_host(request.host):
                return jsonify(error="forbidden"), 403
            return fn(*a, **kw)
        return wrapped

    @app.errorhandler(QueueError)
    def queue_error(e):
        code = e.args[0]
        return jsonify(error=code), 403 if code == "forbidden" else 400

    for page in ("admin", "tv", "print"):
        app.add_url_rule(f"/{page}", page, lambda page=page: send_from_directory(static, f"{page}.html"))
    app.add_url_rule("/", "guest", lambda: send_from_directory(static, "guest.html"))

    @app.get("/library/<slug>/<name>")
    def library_file(slug, name):
        if slug not in songs or name not in LIBRARY_FILES:
            abort(404)
        return send_from_directory(root / "library" / slug, name)

    @app.get("/api/search")
    def api_search():
        q = request.args.get("q", "")[:80]
        with lock:
            refresh_library()
            return jsonify(songs=[mark(v) for v in catalog.search(q, **filters())], artists=catalog.artists(q))

    @app.get("/api/browse")
    def api_browse():
        """A shelf of songs to scroll (?shelf=top&page=0), or every song by one artist (?artist=Queen)."""
        page = request.args.get("page", "0")
        page = int(page) if page.isdigit() else 0
        with lock:
            refresh_library()
            artist = request.args.get("artist")
            rows = (catalog.by_artist(artist, **filters()) if artist else
                    catalog.shelf(request.args.get("shelf", "top"), page=page, popular=popular(), **filters()))
            return jsonify(songs=[mark(v) for v in rows])

    @app.get("/api/state")
    def api_state():
        device = request.args.get("device")
        with lock:
            return jsonify(queue=[view(e, device) for e in party.upcoming()], now_playing=playing(device),
                           paused=party.paused, volume=party.volume, help_vocals=party.help_vocals,
                           join_url=join_url(),  # the Wi-Fi password is for the TV and table cards, not the internet
                           wifi={"name": settings["wifi_name"], "password": "" if via_internet() else settings["wifi_password"]},
                           pub_name=settings["pub_name"], look={k: settings[k] for k in ("look", "accent", "icon")},
                           shelves=settings["shelves"], upnext_seconds=settings["upnext_seconds"],
                           songs_per_singer=settings["songs_per_singer"], nudge=party.nudge, synctest=party.synctest,
                           display={**DEFAULT_DISPLAY, **settings.get("display", {})}, maker={**making, "pct": progress()} if making else {},
                           rules={k: settings[k] for k in ("max_wait_seconds", "hide_explicit", "languages", "auto_download", "library_max_gb")})

    @app.post("/api/queue")
    def api_add():
        """A guest picks a song: from the library (song_id) or from the whole list (catalog_id).
        A song nobody has made yet is checked for timed lyrics first, then made before the guest's turn."""
        b = body()
        name, device, cid = b.get("name"), b.get("device", ""), b.get("catalog_id")
        if not cid:
            with lock:
                return jsonify(view(party.add(name, device, b.get("song_id")), device))
        clean_name(name)
        with lock:
            refresh_library()
            row = catalog.get(str(cid))
            if not row:
                raise QueueError("unknown_song")
            if row["status"] == "ready":
                entry = party.add(name, device, row["slug"], catalog=row["id"])
                remember_pick(row["id"])
                return jsonify(view(entry, device))
            text = f"{row['artist']} - {row['title']}"
            party.check(name, "", text)  # over the limit or already queued: say so before the slow checks
            known = status.get(row["id"]) or ("failed" if text in gave_up() else None)
        if known is None:  # the network checks run outside the lock so other phones aren't held up
            ok = has_synced_lyrics(row["artist"], row["title"])
            if ok is None:
                raise QueueError("offline")
            if not ok:
                known = "no_lyrics"
                with lock:
                    status[row["id"]] = known
                    write_json(status_file, status)
        if known:  # can't be made: the guest may still sing along to a YouTube karaoke video
            if not b.get("video"):
                raise QueueError("no_lyrics")
            yt = karaoke_videos(text)
            if not yt:
                raise QueueError("no_video")
            with lock:
                entry = party.add(name, device, "", wish=text, yt=yt, catalog=row["id"], video=True)
                remember_pick(row["id"])
                return jsonify(view(entry, device))
        with lock:
            entry = party.add(name, device, "", wish=text, catalog=row["id"])
            remember_pick(row["id"])
            out = view(entry, device)
            hurry()
        wake.set()
        threading.Thread(target=find_videos, args=(text,), daemon=True).start()
        return jsonify(out)

    @app.delete("/api/queue/<entry_id>")
    def api_remove(entry_id):
        with lock:
            party.remove(entry_id, device=request.args.get("device"))
        return jsonify(ok=True)

    @app.post("/api/wish")
    def api_wish():
        b = body()
        text = " ".join(re.sub("[–—]", "-", str(b.get("text", ""))).split())[:120]  # "ABBA – Waterloo" -> "ABBA - Waterloo"
        if not text or text.startswith("RETIME "):  # that's a command to the song maker, for staff only
            return jsonify(error="empty"), 400
        with lock:
            party.check(b.get("name"), "", text)  # fail fast, before the slow YouTube search
            hopeless = text in gave_up()  # tried tonight and couldn't be made
            wishes = root / "wishes.txt"
            known = wishes.read_text(encoding="utf-8").splitlines() if wishes.exists() else []
            if not hopeless and text not in known and len(known) < 1000:
                with wishes.open("a", encoding="utf-8") as f:
                    f.write(text + "\n")  # the nightly maker run picks it up even if tonight's attempt fails
        yt = karaoke_videos(text)
        if hopeless and not yt:
            raise QueueError("no_video")
        with lock:
            entry = party.add(b.get("name"), b.get("device", ""), "", wish=text, yt=yt, video=hopeless)
            out = view(entry, b.get("device"))
            if not hopeless:
                hurry()
        wake.set()
        return jsonify(out)

    @app.post("/api/next")
    @tv_only
    def api_next():
        with lock:
            party.next()
            return jsonify(entry=playing())

    @app.post("/api/done")
    @tv_only
    def api_done():
        b = body()
        with lock:
            if b.get("error") and party.now_playing:  # the TV skipped a song it couldn't load: say why in the server window
                print(f"Skipped {party.now_playing['song_id'] or party.now_playing.get('wish')}:{str(b['error'])[:200]} ({request.user_agent.string[:120]})", flush=True)
            return jsonify(ok=party.done(b.get("id")))

    @app.post("/api/admin/check")
    @admin
    def admin_check():
        return jsonify(ok=True)

    @app.post("/api/admin/skip")
    @admin
    def admin_skip():
        return jsonify(ok=party.done(body().get("id")))

    @app.post("/api/admin/pause")
    @admin
    def admin_pause():
        party.paused = bool(body().get("paused"))
        party.save()
        return jsonify(ok=True)

    @app.post("/api/admin/pin")
    @admin
    def admin_pin():
        party.pin(body().get("id"))
        return jsonify(ok=True)

    @app.post("/api/admin/remove")
    @admin
    def admin_remove():
        party.remove(body().get("id"), staff=True)
        return jsonify(ok=True)

    def level():
        try:
            return min(1.0, max(0.0, float(body().get("level"))))
        except (TypeError, ValueError):
            raise QueueError("bad_level")

    @app.post("/api/admin/volume")
    @admin
    def admin_volume():
        party.volume = level()
        party.save()
        return jsonify(ok=True)

    def update_playing_song(**fields):
        """Staff changes to the playing song are kept in its song.json for next time. A YouTube wish has no song.json."""
        slug = party.now_playing and party.now_playing["song_id"]
        if slug not in songs:
            return
        songs[slug].update(fields)
        f = root / "library" / slug / "song.json"
        write_json(f, {**json.loads(f.read_text(encoding="utf-8")), **fields}, indent=1)

    @app.post("/api/admin/help_vocals")
    @admin
    def admin_help_vocals():
        party.help_vocals = level()
        party.save()
        update_playing_song(help_vocals=party.help_vocals)
        return jsonify(ok=True)

    @app.post("/api/admin/nudge")
    @admin
    def admin_nudge():
        """Lyrics earlier (+) or later (-) for the playing song, by staff ear."""
        delta = body().get("delta")
        if not party.now_playing or not party.now_playing["song_id"] or number(-1, 1)(delta) is None:
            raise QueueError("bad_level")
        party.nudge = round(max(-5.0, min(5.0, party.nudge + delta)), 2)
        party.save()
        update_playing_song(sync={**songs.get(party.now_playing["song_id"], {}).get("sync", {}), "nudge": party.nudge})
        return jsonify(ok=True, nudge=party.nudge)

    def song_name(slug):
        s = songs.get(slug, {})
        return f"{s.get('artist', '')} - {s.get('title', '')}"

    @app.get("/api/admin/songs")
    @admin
    def admin_songs():
        """For the staff page: what the song maker is doing, songs whose timing may be guessed, songs it couldn't make."""
        aligned = lambda s: s.get("sync", {}).get("aligned")  # None: made before timing was checked
        weak = sorted((aligned(s) or 0, slug) for slug, s in songs.items() if (aligned(s) or 0) < 0.5)
        failed_rows = [{**(catalog.get(cid) or {"artist": "", "title": cid}), "id": cid, "why": why} for cid, why in status.items()]
        upcoming = [e["wish"] for e in party.upcoming() if e.get("wish") and not party.ready(e) and not e.get("video")]
        return jsonify(making={**making, "pct": progress()} if making else {}, next=upcoming + [f"Re-time: {song_name(s)}" for s in retimes],
                       weak=[{"slug": slug, "name": song_name(slug), "aligned": aligned(songs[slug])} for _, slug in weak],
                       failed=failed_rows, disk_gb=round(library_gb(library), 1))

    @app.post("/api/admin/retime")
    @admin
    def admin_retime():
        slug = body().get("slug")
        if not isinstance(slug, str) or slug not in songs:
            raise QueueError("not_found")
        if slug not in retimes:
            retimes.append(slug)
        wake.set()
        return jsonify(ok=True)

    @app.post("/api/admin/retry")
    @admin
    def admin_retry():
        """A song the maker gave up on may be picked (and made) again, e.g. after a yt-dlp update."""
        cid = str(body().get("id"))
        status.pop(cid, None)
        write_json(status_file, status)
        row = catalog.get(cid)
        if row:  # tonight's tries are forgotten too, so the maker will try it again
            failed.pop(f"{row['artist']} - {row['title']}", None)
        return jsonify(ok=True)

    @app.post("/api/admin/delete_song")
    @admin
    def admin_delete_song():
        """A badly made song leaves the library; picking it again makes it afresh."""
        slug = body().get("slug")
        if not isinstance(slug, str) or slug not in songs or (party.now_playing and party.now_playing["song_id"] == slug):
            raise QueueError("not_found")
        shutil.rmtree(library / songs[slug]["id"], ignore_errors=True)  # the folder we loaded, never a path sent to us
        refresh_library(force=True)
        return jsonify(ok=True)

    @app.post("/api/admin/synctest")
    @admin
    def admin_synctest():
        party.synctest = body().get("on") is True
        return jsonify(ok=True)

    @app.post("/api/admin/settings")
    @admin
    def admin_settings():
        settings.update(merge_settings(settings, body()))
        party.songs_per_singer, party.max_wait = settings["songs_per_singer"], settings["max_wait_seconds"]
        wake.set()  # auto-download may have been switched on
        if not write_json(root / "settings.json", settings, indent=1):
            print("warning: could not save settings.json; the change holds until the app restarts")
        return jsonify(ok=True)

    app.config["settings"] = settings
    return app


if __name__ == "__main__":
    import waitress
    here = Path(__file__).resolve().parent
    app = create_app(here)
    port = app.config["settings"]["port"]
    try:
        sock = bind_exclusive(port)
    except OSError:
        raise SystemExit(f"Port {port} is taken: Pub Karaoke is already running, or another program uses it (on macOS, "
                         f"AirPlay Receiver uses 5000). Close it, or set another \"port\" in settings.json.")
    guests = app.config["settings"]["public_url"] or f"http://{lan_ip()}:{port}/"
    print(f"Pub Karaoke running. Guests: {guests}   TV: http://localhost:{port}/tv")
    app.config["start_tunnel"]()
    # phones poll every 2 s and keep connections open: allow plenty, drop idle ones fast; ident "": no Server header
    waitress.serve(app, sockets=[sock], threads=16, connection_limit=500, channel_timeout=30, ident="")
