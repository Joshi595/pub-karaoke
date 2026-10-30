"""Song maker: turns 'Artist - Title' lines into karaoke folders in library/.

Run: .venv-maker\\Scripts\\python make_songs.py [--limit N] [--only "Artist - Title"] [--model medium]
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KARAFUN_LIST = "https://www.karafun.com/karaoke-song-list.html"  # the free CSV of ~90,000 songs guests search

# ---------------------------------------------------------------- helpers

THEME_NAMES = {"celtic", "neon80s", "disco", "rock", "ballad", "pop", "cover"}
SECTION_HINTS = {"irish": ("celtic", None), "german": ("disco", "de")}


def parse_song_list(text):
    songs, hint, lang = [], None, None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            name = line[1:].strip().lower()
            hint, lang = next((v for k, v in SECTION_HINTS.items() if k in name), (None, None))
            continue
        line_hint = hint
        if "|" in line:
            line, override = line.rsplit("|", 1)
            line = line.strip()
            if override.strip() in THEME_NAMES:  # wishes come from guests: only real theme names count
                line_hint = override.strip()
        artist, sep, title = line.partition(" - ")
        if not sep:  # free-text wish: let the lyrics search work out artist/title
            artist, title = "", line
        songs.append({"artist": artist.strip(), "title": title.strip(), "hint": line_hint, "lang": lang})
    return songs


LRC_TIME = re.compile(r"\[(\d+):(\d+(?:\.\d+)?)\]")


def parse_lrc(text):
    out = []
    for line in text.splitlines():
        stamps = LRC_TIME.findall(line)
        if not stamps:
            continue
        words = LRC_TIME.sub("", line).strip()
        out += [(round(int(m) * 60 + float(s), 2), words) for m, s in stamps]
    return sorted(out, key=lambda x: x[0])


def build_lines(lrc, duration):
    lines = []
    for i, (t, text) in enumerate(lrc):
        if text:
            nxt = lrc[i + 1][0] if i + 1 < len(lrc) else duration
            lines.append({"start": t, "next": nxt, "text": text})
    return lines


HOP = 0.02  # seconds per loudness frame of the vocal track


def spread_words(start, end, text, loud=None):
    """Guessed word times for a line the aligner couldn't time: the words share out the moments the voice is
    audible in the window, by length. With no voice to go by, ~0.6 s per word from the line start."""
    words = text.split()
    total = sum(len(w) for w in words) or 1
    frames = [i for i in range(int(start / HOP), int(end / HOP)) if loud and i < len(loud) and loud[i]]
    out, done = [], 0
    if len(frames) >= 5 * len(words):
        n = len(frames)
        for w in words:
            a = int(n * done / total)
            done += len(w)
            b = max(a + 1, int(n * done / total))
            out.append({"w": w, "t": round(frames[a] * HOP, 2), "e": round(frames[b - 1] * HOP + HOP, 2)})
        return out
    window = min(end - start, 0.6 * len(words) + 1.0)
    for w in words:
        t = start + window * done / total
        done += len(w)
        out.append({"w": w, "t": round(t, 2), "e": round(max(t + 0.1, start + window * done / total), 2)})
    return out


def norm_word(w):
    return re.sub(r"[^\w]", "", w.lower())


def line_offsets(lines, heard):
    """How far each line sits from the lyric file's time in this recording, from the words the transcriber heard.
    The five nearest heard lines vote (median), so one misheard line can't move it, and a version with a longer
    intro or an extra chorus still lines up. None when too little was heard to trust it."""
    from difflib import SequenceMatcher
    from statistics import median
    lyric = [(i, k, norm_word(w)) for i, l in enumerate(lines) for k, w in enumerate(l["text"].split()) if norm_word(w)]
    said = [(norm_word(w), s) for w, s, _ in heard if norm_word(w)]
    match = SequenceMatcher(None, [x[2] for x in lyric], [x[0] for x in said], autojunk=False)
    raw = {}
    for a, b, n in match.get_matching_blocks():
        for j in range(n):
            i, k, _ = lyric[a + j]
            if k == 0:  # the line's first word was heard: the line starts there
                raw.setdefault(i, said[b + j][1] - lines[i]["start"])
    if len(raw) < 3:
        return None
    # ponytail: O(lines^2) nearest-neighbour vote, fine for a song's ~60 lines
    return [round(median(raw[k] for k in sorted(raw, key=lambda k: abs(k - i))[:5]), 2) for i in range(len(lines))]


def heard_starts(heard):
    """When the transcriber heard each word, and each pair of words, begin."""
    said = [(norm_word(w), s) for w, s, _ in heard if norm_word(w)]
    starts = {}
    for j, (w, s) in enumerate(said):
        starts.setdefault((w,), []).append(s)
        if j + 1 < len(said):
            starts.setdefault((w, said[j + 1][0]), []).append(s)
    return starts


def line_key(line):
    return tuple(norm_word(w) for w in line["text"].split() if norm_word(w))[:2]


def vote_offsets(lines, heard, near=6.0):
    """Line offsets by vote: every place a line's first two words were heard votes for a shift, the shift most lines
    agree on wins, and each line takes its nearest hearing to it. A misheard chorus can't drag lines onto
    another chorus, which can happen to line_offsets; on a song that repeats one line, line_offsets does better."""
    from collections import Counter
    from statistics import median
    starts = heard_starts(heard)
    cands = {i: [s - l["start"] for s in starts.get(line_key(l), [])] for i, l in enumerate(lines)}
    votes = Counter(b for c in cands.values() for b in {round(x) for x in c})
    if not votes:
        return None
    shift = max(votes, key=lambda b: votes[b - 1] + votes[b] + votes[b + 1])
    raw = {i: min(c, key=lambda x: abs(x - shift)) for i, c in cands.items() if c and min(abs(x - shift) for x in c) <= near}
    if len(raw) < 3:
        return None
    return [round(median(raw[k] for k in sorted(raw, key=lambda k: abs(k - i))[:5]), 2) for i in range(len(lines))]


def heard_at(lines, heard, offsets, starts=None):
    """How many lines the transcriber heard begin within a second of where the offsets put them."""
    starts = starts or heard_starts(heard)
    return sum(any(abs(s - l["start"] - o) <= 1.0 for s in starts.get(line_key(l), [])) for l, o in zip(lines, offsets))


def best_fit(cands, heard):
    """The lyric file and line offsets that put the most lines where they're heard. The lyrics site's uploads of a
    song differ (album version, single edit) and its durations can't be trusted; ties go to the shorter file."""
    starts = heard_starts(heard)
    tries = [(lines, offs) for lines in cands
             for offs in (line_offsets(lines, heard), vote_offsets(lines, heard), [0.0] * len(lines)) if offs]
    return max(tries, key=lambda t: (heard_at(t[0], heard, t[1], starts), -len(t[0])))


def windows(lines, offsets, duration):
    """Each line's stretch of the recording: from just before its shifted start up to the next line's, in order,
    never overlapping, and no longer than the words could take."""
    out, prev = [], 0.0
    for i, l in enumerate(lines):
        start = max(prev, min(l["start"] + offsets[i] - 0.3, duration - 0.1))
        nxt = lines[i + 1]["start"] + offsets[i + 1] - 0.3 if i + 1 < len(lines) else duration
        end = max(start + 0.1, min(nxt, l["next"] + offsets[i], start + 2.0 * len(l["text"].split()) + 4, duration))
        out.append({"start": round(start, 2), "end": round(end, 2), "text": l["text"]})
        prev = out[-1]["end"]
    return out


def good_line(words, win):
    """Trust the aligner only when it's confident, in order, inside the window, and hasn't squashed words to nothing."""
    if not words:
        return False
    squashed = sum(w["e"] - w["t"] < 0.05 for w in words)
    return (sum(w["p"] for w in words) / len(words) >= 0.45 and squashed <= len(words) // 4
            and all(a["t"] <= b["t"] for a, b in zip(words, words[1:]))
            and win["start"] - 0.05 <= words[0]["t"] and words[-1]["e"] <= win["end"] + 0.05)


def trim_to_voice(t, e, loud):
    """A word's wipe ends when the voice does, not when the next word starts after a breath or a solo."""
    voiced = [i for i in range(int(t / HOP), int(e / HOP)) if loud and i < len(loud) and loud[i]]
    return round(min(e, max(t + 0.1, (voiced[-1] + 1) * HOP)), 2) if voiced else e


def merge_alignment(lines, wins, aligned, loud=None):
    """The lyrics as the TV shows them, and the share of lines timed by ear rather than guessed."""
    out, good = [], 0
    for i, (line, win) in enumerate(zip(lines, wins)):
        words = aligned[i] if aligned and i < len(aligned) else None
        if good_line(words, win):
            good += 1
            words = [{"w": w["w"], "t": w["t"], "e": trim_to_voice(w["t"], w["e"], loud)} for w in words]
        else:
            words = spread_words(win["start"], win["end"], win["text"], loud)
        out.append({"start": words[0]["t"], "end": words[-1]["e"], "lrc": line["start"], "text": line["text"], "words": words})
    return out, round(good / max(1, len(lines)), 2)


def last_line(lrc):
    return max((t for t, text in parse_lrc(lrc["syncedLyrics"]) if text), default=0.0)


def fits(lrc, video_duration, tol):
    """A video fits a lyric file when it outlasts the last line and has the length the lyrics site gives, or ends
    within a minute of the last line: the site's length can be wrong (album lyrics tagged with the single's length)."""
    last = last_line(lrc)
    return video_duration > last and (abs(lrc["duration"] - video_duration) <= tol or 0 < last and video_duration <= last + 60)


def pick_pairs(lrc_cands, yt_cands, tol=3.0):
    """(lyrics, video) pairs closest in duration first, one per video, so a video whose singing doesn't match can be swapped."""
    pairs = sorted(((abs(lrc["duration"] - yt["duration"]), li, lrc, yt) for li, lrc in enumerate(lrc_cands)
                    if lrc.get("syncedLyrics") and lrc.get("duration") for yt in yt_cands
                    if yt.get("duration") and fits(lrc, yt["duration"], tol)), key=lambda p: (p[0], p[1]))
    seen, out = set(), []
    for _, _, lrc, yt in pairs:
        if yt["id"] not in seen:
            seen.add(yt["id"])
            out.append((lrc, yt))
    return out


def pick_pair(lrc_cands, yt_cands, tol=3.0):
    pairs = pick_pairs(lrc_cands, yt_cands, tol)
    return pairs[0] if pairs else None


BAD_VIDEO = re.compile(r"\b(karaoke|instrumental|live|cover|remix|8d|sped up)\b", re.I)


def usable_video(title, wanted_title):
    wanted = wanted_title.lower()
    return all(m.lower() in wanted for m in BAD_VIDEO.findall(title))


def pick_itunes(results, artist):
    mine = [r for r in results if artist.lower() in r.get("artistName", "").lower()]
    if not mine:
        return None
    years = [int(r["releaseDate"][:4]) for r in mine if r.get("releaseDate")]
    return {
        "genre": mine[0].get("primaryGenreName", ""),
        "year": min(years) if years else None,
        "cover": mine[0].get("artworkUrl100", "").replace("100x100", "600x600"),
    }


# Common little words that give a language away; the word timing needs to know which language it's listening to.
LANG_WORDS = {
    "en": "the and you i me my is it we your don't love",
    "de": "und ich die der das nicht du ist wir mich mir sie",
    "fr": "je tu et les des que qui pas est mon moi toi une",
    "es": "el los las y que en mi yo por con amor tú",
    "it": "il che non sono mi ti per con ma io della",
    "pt": "o os não eu você meu minha com para é",
    "nl": "het een ik je niet van dat mijn wat",
}
LANG_WORDS = {k: set(v.split()) for k, v in LANG_WORDS.items()}


def guess_lang(text):
    words = re.findall(r"[^\W\d_]+(?:'t)?", text.lower())
    counts = {lang: sum(w in stop for w in words) for lang, stop in LANG_WORDS.items()}
    return max(counts, key=lambda lang: (counts[lang], lang == "en"))


def pick_theme(hint, genre, year, lang, tags=(), country=None):
    genre = (genre or "").lower()
    tags = [t.lower() for t in tags]
    has = lambda text, *keys: any(k in text for k in keys)
    if hint in THEME_NAMES:
        return hint
    if country == "IE" or any(has(t, "irish", "celtic") for t in tags):
        return "celtic"
    if "schlager" in tags or "schlager" in genre:
        return "disco"
    if has(genre, "rock", "metal", "punk", "alternative"):
        return "rock"
    if any(t in ("neue deutsche welle", "new wave", "synth-pop") for t in tags) or (year and 1978 <= year <= 1991):
        return "neon80s"
    if lang == "de":
        return "disco"
    if has(genre, "celtic", "folk"):
        return "celtic"
    if "ballad" in tags or has(genre, "singer/songwriter", "soundtrack", "vocal", "jazz"):
        return "ballad"
    if has(genre, "pop", "dance", "electronic", "hip-hop", "r&b"):
        return "pop"
    return "cover"


def pick_wish(wish, cands):
    """A free-text wish -> the LRCLIB result that really resembles it, else None: no song beats the wrong song."""
    from difflib import SequenceMatcher
    w = " ".join(wish.lower().split())
    def score(c):
        title = c["trackName"].split("(")[0].lower().strip()  # "(feat. ...)" isn't what guests type
        artist = c["artistName"].lower()
        if len(w) >= 4 and title.startswith(w):
            return 1.0
        return max(SequenceMatcher(None, w, s).ratio() for s in (title, f"{artist} {title}", f"{title} {artist}"))
    best = max(cands, key=score, default=None)
    return best if best and score(best) >= 0.6 else None


def slugify(artist, title):
    s = f"{artist} {title}".lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


# ---------------------------------------------------------------- pipeline (network, ffmpeg, AI)

UA = {"User-Agent": "PubKaraoke/1.0 (https://github.com/Joshi595/pub-karaoke)"}  # MusicBrainz asks for a contact
_mb_last = [0.0]
_separator = [None]


def fetch_lrclib(artist, title):
    import requests
    params = {"artist_name": artist, "track_name": title} if artist else {"q": title}
    for attempt in range(4):  # LRCLIB sometimes refuses briefly; a refusal is not "no lyrics"
        try:
            r = requests.get("https://lrclib.net/api/search", params=params, headers=UA, timeout=20)
            if r.ok and isinstance(r.json(), list):
                return r.json()
        except (requests.RequestException, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    raise ConnectionError("LRCLIB not answering, will retry next run")


def has_synced_lyrics(artist, title, timeout=5):
    """Quick check when a guest picks a song nobody has made yet: True or False, None if LRCLIB can't be reached.
    Standard library only, so the live app can call it without the song maker's packages."""
    import urllib.parse
    import urllib.request
    try:
        for params in ({"artist_name": artist, "track_name": title}, {"q": f"{artist} {title}"}):
            url = "https://lrclib.net/api/search?" + urllib.parse.urlencode(params)
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:  # a fixed https:// address  # nosec B310
                found = [c for c in json.load(r) if c.get("syncedLyrics")]
            if "q" in params:  # the loose search must still be this song
                found = [c for c in found if pick_wish(f"{artist} {title}", [c])]
            if found:
                return True
        return False
    except (OSError, ValueError):
        return None


def fetch_itunes(artist, title):
    import requests
    try:
        r = requests.get("https://itunes.apple.com/search", params={"term": f"{artist} {title}", "entity": "song", "limit": 5}, timeout=20)
        return r.json().get("results", [])
    except Exception:
        return []


def fetch_mb_artist(artist):
    import requests
    for _ in range(3):
        time.sleep(max(0.0, _mb_last[0] + 1.1 - time.time()))
        _mb_last[0] = time.time()
        try:
            d = requests.get("https://musicbrainz.org/ws/2/artist/", params={"query": f'artist:"{artist}"', "fmt": "json", "limit": 1}, headers=UA, timeout=20).json()
        except Exception:
            continue
        if "error" in d:
            continue
        if not d.get("artists"):
            return None
        a = d["artists"][0]
        tags = sorted(a.get("tags", []), key=lambda t: -t.get("count", 0))
        return {"country": a.get("country"), "tags": [t["name"].lower() for t in tags]}
    return None


YDL_BASE = {"quiet": True, "no_warnings": True, "js_runtimes": {"node": {}}}


def search_youtube(query, wanted_title):
    import yt_dlp
    with yt_dlp.YoutubeDL({**YDL_BASE, "extract_flat": True}) as ydl:
        entries = ydl.extract_info(f"ytsearch8:{query}", download=False).get("entries") or []
    return [{"id": e["id"], "title": e.get("title", ""), "duration": e.get("duration")}
            for e in entries if e and usable_video(e.get("title", ""), wanted_title)]


def download_audio(video_id, dest_noext):
    import yt_dlp
    with yt_dlp.YoutubeDL({**YDL_BASE, "format": "bestaudio/best", "outtmpl": str(dest_noext) + ".%(ext)s"}) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return next(dest_noext.parent.glob(dest_noext.name + ".*"))


def normalize(src, dst_wav):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "44100", "-ac", "2", str(dst_wav)], check=True)


def separate(wav, outdir, overlap=8):
    import torch
    from audio_separator.separator import Separator
    if _separator[0] is None:
        # overlap: how many times each slice of audio is processed; 8 = best, 2 = ~1.8x faster with a little more vocal bleed
        # use_autocast: half precision on the graphics card, ~2.2x faster with an identical-sounding result (measured)
        _separator[0] = Separator(output_dir=str(outdir), output_format="m4a", use_autocast=torch.cuda.is_available(), mdxc_params={
            "segment_size": 256, "override_model_segment_size": False, "batch_size": None, "overlap": overlap, "pitch_shift": 0})
        _separator[0].load_model()
    sep = _separator[0]
    sep.output_dir = str(outdir)
    sep.model_instance.output_dir = str(outdir)
    sep.separate(str(wav), {"Vocals": "vocals", "Instrumental": "instrumental"})
    return outdir / "instrumental.m4a", outdir / "vocals.m4a"


def voice_frames(vocals):
    """True for every HOP of the vocal track where someone is singing (within 25 dB of the loud parts)."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(vocals), "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = int(16000 * HOP)
    db = 20 * np.log10(np.sqrt((x[:len(x) // n * n].reshape(-1, n) ** 2).mean(1)) + 1e-6)
    return (db > np.percentile(db, 90) - 25).tolist()


def listen(model, vocals, cands, lang, duration):
    """Find where each line is sung in this recording, then time its words inside that window. `cands` are the
    lyric files to choose from, best guess first. Whole-song alignment piles the words up on sung vocals; one
    window per line can't spoil the rest."""
    import torch
    gpu = torch.cuda.is_available()
    lines = cands[0]
    try:
        if gpu:  # the timing model only borrows the graphics card; the separator needs all of its memory otherwise
            model.to("cuda")
        heard = [(w.word, w.start, w.end) for w in model.transcribe(str(vocals), language=lang, vad=True, verbose=None).all_words()]
        lines, offsets = best_fit(cands, heard)
        wins = windows(lines, offsets, duration)
        result = model.align_words(str(vocals), wins, lang, regroup=False, verbose=None)
    except Exception as e:
        print("   timing failed:", e)
        return lines, windows(lines, [0.0] * len(lines), duration), None
    finally:
        if gpu:
            model.to("cpu")
            torch.cuda.empty_cache()
    aligned = [[{"w": w.word.strip(), "t": round(w.start, 2), "e": round(w.end, 2), "p": w.probability}
                for w in (seg.words or []) if w.word.strip()] for seg in result.segments]
    return lines, wins, aligned if len(aligned) == len(wins) else None


def time_lyrics(model, vocals, cands, lang, duration):
    lines, wins, aligned = listen(model, vocals, cands, lang, duration)
    return merge_alignment(lines, wins, aligned, voice_frames(vocals))


def other_lyrics(lrc_cands, duration, skip=None, most=6):
    """Line lists of the lyrics site's other uploads of a song, to choose from by ear."""
    texts = dict.fromkeys(c["syncedLyrics"] for c in lrc_cands if c.get("syncedLyrics") and c["syncedLyrics"] != skip)
    return [l for l in (build_lines(parse_lrc(t), duration) for t in list(texts)[:most]) if l]


def write_atomic(path, text):
    """The live app may be sending this file to the TV right now: swap it in whole, never half-written."""
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    for attempt in range(5):  # Windows refuses the swap while the file is being read
        try:
            return os.replace(tmp, path)
        except PermissionError:
            time.sleep(0.2 * (attempt + 1))
    raise PermissionError(f"{path} is in use")


def retime(slugs, library, model):
    """Time existing songs again from their vocal track, without downloading anything. Returns how many worked."""
    done = 0
    for slug in slugs:
        d = library / slug
        try:
            song = json.loads((d / "song.json").read_text(encoding="utf-8"))
            old = json.loads((d / "lyrics.json").read_text(encoding="utf-8"))
            backup = d / "lyrics-v1.json"
            if not backup.exists() and "sync" not in song:  # keep the first version in case the new timing is worse
                backup.write_text(json.dumps(old, ensure_ascii=False), encoding="utf-8")
            lines = build_lines(sorted((l.get("lrc", l["start"]), l["text"]) for l in old), song["duration"])
            t0 = time.time()
            before, old_lang = song.get("sync", {}).get("aligned", 0), song.get("lang")
            try:  # another upload on the lyrics site may fit this recording better (single edit vs album version)
                cands = [lines] + other_lyrics(fetch_lrclib(song["artist"], song["title"]), song["duration"])
            except ConnectionError:
                cands = [lines]
            lang = guess_lang(" ".join(l["text"] for l in lines))  # songs made before French etc. were known
            lyrics, score = time_lyrics(model, d / "vocals.m4a", cands, lang, song["duration"])
            if score < 0.5 and old_lang and old_lang != lang:  # the guess can be wrong (bilingual songs): try the old one
                other = time_lyrics(model, d / "vocals.m4a", cands, old_lang, song["duration"])
                if other[1] > score:
                    (lyrics, score), lang = other, old_lang
            if score < before:  # never swap good timing for worse
                print(f"kept the earlier timing ({before:.0%} > {score:.0%})  {slug}", flush=True)
                done += 1
                continue
            song["lang"] = lang
            write_atomic(d / "lyrics.json", json.dumps(lyrics, ensure_ascii=False))
            song["sync"] = {**song.get("sync", {}), "v": 2, "aligned": score}
            write_atomic(d / "song.json", json.dumps(song, ensure_ascii=False, indent=1))
            print(f"{score:4.0%} timed by ear  {slug}  ({time.time() - t0:.0f}s)", flush=True)
            done += 1
        except Exception as e:
            print(f"skip: error {type(e).__name__}: {e}  {slug}", flush=True)
    return done


def remake(slugs, library, work, model, overlap):
    """Make songs again from other recordings and keep whichever times better: the first one found can be
    another version than the lyrics (single edit, live take, another language). Returns how many got better."""
    better = 0
    for slug in slugs:
        d, trial = library / slug, work / "remake"
        try:
            old = json.loads((d / "song.json").read_text(encoding="utf-8"))
            before = (old.get("sync") or {}).get("aligned") or 0
            shutil.rmtree(trial, ignore_errors=True)
            same = lambda yt: yt["id"] == old.get("video") or float(yt["duration"]) == old["duration"]
            result = make_song({"artist": old["artist"], "title": old["title"], "hint": None, "lang": old.get("lang")},
                               trial, work, model, overlap, skip=same, tries=3, good_enough=max(0.8, before))
            made = next(trial.glob("*/song.json"), None) if result == "ok" else None
            new = json.loads(made.read_text(encoding="utf-8")) if made else {}
            score = (new.get("sync") or {}).get("aligned", 0)
            if score <= before:
                print(f"kept the old recording ({before:.0%}, other: {score:.0%} {result})  {slug}", flush=True)
                continue
            # staff's look and help-vocal level stay; the old nudge was for the old recording
            song = {**old, **{k: new[k] for k in ("duration", "lang", "sync", "video") if k in new}}
            made.write_text(json.dumps(song, ensure_ascii=False, indent=1), encoding="utf-8")
            gone = work / "replaced" / slug
            shutil.rmtree(gone, ignore_errors=True)
            gone.parent.mkdir(parents=True, exist_ok=True)
            os.replace(d, gone)
            os.replace(made.parent, d)
            print(f"{before:.0%} -> {score:.0%} with another recording  {slug}", flush=True)
            better += 1
        except Exception as e:
            print(f"skip: error {type(e).__name__}: {e}  {slug}", flush=True)
    return better


def make_song(req, library, work, model, overlap=8, progress=lambda stage, pct: None, skip=lambda yt: False, tries=2, good_enough=0.3):
    artist, title = req["artist"], req["title"]
    if artist and (library / slugify(artist, title)).exists():
        return "exists"
    progress("lyrics", 5)
    lrc_cands = fetch_lrclib(artist, title)
    if artist and not any(c.get("syncedLyrics") for c in lrc_cands):
        # the song list spells it "AC / DC", LRCLIB "AC/DC": search loosely, but keep the list's name for the folder
        loose = [c for c in fetch_lrclib("", f"{artist} {title}") if c.get("syncedLyrics")]
        best = pick_wish(f"{artist} {title}", loose)
        lrc_cands = [c for c in loose if best and (c["artistName"], c["trackName"]) == (best["artistName"], best["trackName"])]
    if not artist:  # free-text wish: take artist/title from the best lyrics match
        best = pick_wish(title, [c for c in lrc_cands if c.get("syncedLyrics")])
        if not best:
            return "skip: no lyrics found that match the wish"
        artist, title = best["artistName"], best["trackName"]
        req["artist"], req["title"] = artist, title  # so main() can say which library folder this wish became
        lrc_cands = [c for c in lrc_cands if c["artistName"] == artist and c["trackName"] == title]
        if (library / slugify(artist, title)).exists():
            return "exists"
    if not any(c.get("syncedLyrics") for c in lrc_cands):
        return "skip: no synced lyrics on LRCLIB"
    progress("search", 10)
    pairs = []
    for query in (f"{artist} {title} official audio", f"{artist} {title} lyrics"):
        pairs = [p for p in pick_pairs(lrc_cands, search_youtube(query, title)) if not skip(p[1])]
        if pairs:
            break
    if not pairs:
        return "skip: no lyrics/audio match"

    slug = slugify(artist, title)
    tmp = work / slug
    shutil.rmtree(tmp, ignore_errors=True)
    best = None  # (score, folder, lyrics, lang, video) of the attempt whose singing matched the lyrics best
    for attempt, (lrc, yt) in enumerate(pairs[:tries]):  # each attempt costs ~2.5 min of vocal removal
        out = tmp / f"out{attempt}"
        try:
            out.mkdir(parents=True)
            progress("download", 15)
            src = download_audio(yt["id"], tmp / f"source{attempt}")
            normalize(src, tmp / "norm.wav")
            progress("separate", 25)
            inst, voc = separate(tmp / "norm.wav", out, overlap)
            progress("timing", 75)
            lines = build_lines(parse_lrc(lrc["syncedLyrics"]), float(yt["duration"]))
            lang = req["lang"] or guess_lang(" ".join(l["text"] for l in lines))
            cands = [lines] + other_lyrics(lrc_cands, float(yt["duration"]), skip=lrc["syncedLyrics"])
            lyrics, score = time_lyrics(model, voc, cands, lang, float(yt["duration"]))
        except Exception:
            if best:  # the second video failing mustn't throw away the first
                break
            raise
        if not best or score > best[0]:
            best = (score, out, lyrics, lang, yt)
        if score >= good_enough:
            break
        # under a third of the lines heard where the lyrics say: probably another version of the song
        print(f"   video {yt['id']}: only {score:.0%} of the lines match the singing, trying another", flush=True)
    score, out, lyrics, lang, yt = best

    progress("finish", 95)
    meta = pick_itunes(fetch_itunes(artist, title), artist) or {"genre": "", "year": None, "cover": ""}
    if meta["cover"]:
        import requests
        r = requests.get(meta["cover"], timeout=20)
        if r.ok:
            (out / "cover.jpg").write_bytes(r.content)
    mb = fetch_mb_artist(artist) or {"tags": [], "country": None}
    song = {"artist": artist, "title": title, "duration": float(yt["duration"]), "year": meta["year"],
            "genre": meta["genre"], "lang": lang,
            "theme": pick_theme(req["hint"], meta["genre"], meta["year"], lang, mb["tags"], mb["country"]),
            "help_vocals": 0.25, "sync": {"v": 2, "aligned": score}, "video": yt["id"]}
    (out / "lyrics.json").write_text(json.dumps(lyrics, ensure_ascii=False), encoding="utf-8")
    (out / "song.json").write_text(json.dumps(song, ensure_ascii=False, indent=1), encoding="utf-8")
    library.mkdir(exist_ok=True)
    os.replace(out, library / slug)  # atomic: a half-made song never shows up in the library
    shutil.rmtree(tmp, ignore_errors=True)
    return "ok"


def log_attention(line, reason):
    f = ROOT / "needs-attention.txt"
    seen = f.read_text(encoding="utf-8") if f.exists() else ""
    if f"\t{line}\t{reason}\n" not in seen:
        with f.open("a", encoding="utf-8") as fh:
            fh.write(f"{date.today()}\t{line}\t{reason}\n")


def library_gb(library):
    return sum(f.stat().st_size for d in library.iterdir() if d.is_dir() for f in d.iterdir() if f.is_file()) / 1e9


def prefetch(n, library, work, model, overlap):
    """What the app makes while it's idle, for the nights it isn't running: up to N songs this pub is likely to
    want, within the disk limit on the staff page."""
    from catalog import Catalog
    read = lambda name, default: json.loads((ROOT / name).read_text(encoding="utf-8-sig")) if (ROOT / name).exists() else default
    settings, status = read("settings.json", {}), read("catalog-status.json", {})
    starter, csv_file = ROOT / "starter-songs.txt", library / "karafuncatalog.csv"
    if not csv_file.exists():
        return print(f"--prefetch picks from the KaraFun song list: save the CSV from {KARAFUN_LIST} as {csv_file}")
    catalog = Catalog(csv_file, starter.read_text(encoding="utf-8") if starter.exists() else "")
    popular = {cid: v[0] for cid, v in read("history.json", {}).items()}
    for _ in range(n):
        if library_gb(library) >= settings.get("library_max_gb", 20):
            return print("disk limit reached")
        catalog.set_library({p.parent.name: json.loads(p.read_text(encoding="utf-8")) for p in library.glob("*/song.json")})
        row = catalog.prefetch(popular, skip=set(status), hide_explicit=settings.get("hide_explicit", True),
                               langs=settings.get("languages") or None)
        if not row:
            return
        line = f"{row['artist']} - {row['title']}"
        try:
            result = make_song({"artist": row["artist"], "title": row["title"], "hint": None, "lang": None}, library, work, model, overlap)
        except Exception as e:
            result = f"skip: error {type(e).__name__}: {e}"
        print(f"{result:<40} {line}", flush=True)
        if result.startswith("skip"):
            log_attention(line, result[6:])
            status[row["id"]] = "failed"  # the app shows it as video-only; staff can clear it with Try again
            (ROOT / "catalog-status.json").write_text(json.dumps(status), encoding="utf-8")


def serve(library, work, model, overlap):
    """For the live app: make one song per line read from stdin, keeping the AI models loaded in between.
    Prints STAGE <name> <percent> while working, then SLUG <folder> or FAIL <reason>. Stops when stdin closes."""
    import sys
    for line in sys.stdin:
        if line.startswith("RETIME "):  # staff asked for a song's words to be timed again
            slug = line[7:].strip()  # a folder made by slugify, inside library/: never a path
            ok = re.fullmatch(r"[a-z0-9-]+", slug) and (library / slug).is_dir() and retime([slug], library, model)
            print(f"SLUG {slug}" if ok else "FAIL error: could not re-time", flush=True)
            continue
        found = parse_song_list("# Wishes\n" + line.strip())
        if not found:  # e.g. a wish starting with "#": the app waits for an answer, so always give one
            print("FAIL no lyrics found that match the wish", flush=True)
            continue
        req = found[0]
        name = f"{req['artist']} - {req['title']}" if req["artist"] else req["title"]
        try:
            status = make_song(req, library, work, model, overlap, lambda stage, pct: print(f"STAGE {stage} {pct}", flush=True))
        except Exception as e:
            status = f"skip: error {type(e).__name__}: {e}"
        if status in ("ok", "exists"):
            print(f"SLUG {slugify(req['artist'], req['title'])}", flush=True)
        else:
            log_attention(name, status[6:])
            print(f"FAIL {status[6:]}", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Make karaoke songs for the library.")
    ap.add_argument("--limit", type=int, default=0, help="stop after N new songs")
    ap.add_argument("--only", help='make just this "Artist - Title"')
    ap.add_argument("--model", help="stable-ts model (default: medium on GPU, base on CPU)")
    ap.add_argument("--overlap", type=int, default=8, help="vocal separation passes: 8 = best quality, 2 = faster")
    ap.add_argument("--list", help="make the songs in this file instead of starter-songs.txt and wishes.txt, e.g. top-songs.txt")
    ap.add_argument("--retime", nargs="*", metavar="SLUG", help="time the words of made songs again (all songs if no slug given)")
    ap.add_argument("--remake", nargs="+", metavar="SLUG", help="make songs again from another recording, keeping whichever times better")
    ap.add_argument("--serve", action="store_true", help="for the live app: make the songs it sends, one per line")
    ap.add_argument("--prefetch", type=int, metavar="N", help="make up to N songs this pub is likely to want (the app does this when idle)")
    args = ap.parse_args(argv)

    def load_model():
        import stable_whisper
        import torch
        return stable_whisper.load_model(args.model or ("medium" if torch.cuda.is_available() else "base"), device="cpu")

    library, work = ROOT / "library", ROOT / "work"
    if args.retime is not None:
        return retime(args.retime or sorted(p.parent.name for p in library.glob("*/song.json")), library, load_model())
    if args.remake:
        return remake(args.remake, library, work, load_model(), args.overlap)
    if args.serve:
        return serve(library, work, load_model(), args.overlap)
    if args.prefetch:
        return prefetch(args.prefetch, library, work, load_model(), args.overlap)

    read = lambda name: (ROOT / name).read_text(encoding="utf-8") if (ROOT / name).exists() else ""
    if args.list:
        songs = parse_song_list(read(args.list))
    else:
        songs = parse_song_list(read("starter-songs.txt")) + parse_song_list("# Wishes\n" + read("wishes.txt"))
    if args.only:
        wanted = parse_song_list(args.only)[0]
        key = lambda s: (s["artist"].lower(), s["title"].lower())
        songs = [s for s in songs if key(s) == key(wanted)] or [wanted]
    pending = [s for s in songs if not (s["artist"] and (library / slugify(s["artist"], s["title"])).exists())]
    print(f"{len(songs)} songs listed, {len(pending)} to make")
    if not pending:
        if args.only and songs[0]["artist"]:  # a wish for a song that's already made
            print(f"SLUG {slugify(songs[0]['artist'], songs[0]['title'])}", flush=True)
        return

    model = load_model()
    made = 0
    for req in pending:
        line = f"{req['artist']} - {req['title']}" if req["artist"] else req["title"]
        t0 = time.time()
        try:
            status = make_song(req, library, work, model, args.overlap)
        except Exception as e:
            status = f"skip: error {type(e).__name__}: {e}"
        print(f"{status:<40} {line}  ({time.time() - t0:.0f}s)", flush=True)
        if status in ("ok", "exists"):
            print(f"SLUG {slugify(req['artist'], req['title'])}", flush=True)  # read by app.py when it makes a guest's wish
        if status.startswith("skip"):
            log_attention(line, status[6:])
        elif status == "ok":
            made += 1
            if args.limit and made >= args.limit:
                break


if __name__ == "__main__":
    main()
