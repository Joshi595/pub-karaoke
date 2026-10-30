"""Every song a guest can pick: the KaraFun list (~90,000 songs, most popular first), the starter list and the
songs already made. Search forgives typos, accents and word order; shelves give phones something to browse."""
import csv
import math
import re
import unicodedata

from make_songs import slugify

ROCK = {"Rock", "Hard Rock", "Alternative", "Punk/Grunge", "Metal", "Rock 'n Roll", "Soft rock"}
SECTIONS = {"crowd favourites": "classics", "pub classics": "classics", "irish": "irish", "german": "german"}  # starter-songs.txt headers
SHELVES = ("ready", "here", "top", "classics", "irish", "german", "schlager", "80s", "rock", "country", "duets")


def fold(s):
    """What a guest might type for a name: no case, accents or apostrophes, '&' as 'and', and ä/ae/a all alike."""
    s = unicodedata.normalize("NFKD", str(s).lower().replace("ß", "ss")).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", " ", s.replace("&", " and ").replace("'", ""))
    return re.sub(r"([aou])e", r"\1", s).strip()  # "aerzte" = "arzte" = "Ärzte"


class Catalog:
    def __init__(self, csv_path=None, starter_text=""):
        self.rows, self.by_slug, self.by_id = [], {}, {}
        self.keys, self.compact, self.words, self.titles, self.artist_keys = [], [], [], [], []
        if csv_path:
            with open(csv_path, encoding="utf-8-sig", newline="") as f:
                for r in csv.DictReader(f, delimiter=";"):
                    self._add(r["Artist"], r["Title"], id=f"k{r['Id']}", year=int(r["Year"]) if r["Year"].isdigit() else None,
                              styles=[s for s in r["Styles"].split(",") if s], langs=[s for s in r["Languages"].split(",") if s],
                              duo=r["Duo"] == "1", explicit=r["Explicit"] == "1")
        self.irish, section = set(), None
        for line in starter_text.splitlines():
            line = line.split("|")[0].strip()
            if line.startswith("#"):
                section = SECTIONS.get(line[1:].strip().lower())
                continue
            artist, sep, title = line.partition(" - ")
            if sep and section:
                self.rows[self._find_or_add(artist.strip(), title.strip())]["sections"].add(section)
                if section == "irish":
                    self.irish.add(fold(artist))
        self.ready, self.lyrics = set(), {}

    def _add(self, artist, title, id=None, year=None, styles=(), langs=(), duo=False, explicit=False):
        i = len(self.rows)
        slug = slugify(artist, title)
        row = {"id": id or slug, "artist": artist, "title": title, "year": year, "styles": set(styles), "langs": set(langs),
               "duo": duo, "explicit": explicit, "slug": slug, "sections": set()}
        self.rows.append(row)
        self.by_slug.setdefault(slug, i)
        self.by_id[row["id"]] = i
        key = fold(f"{artist} {title}")
        self.keys.append(key)
        self.compact.append(key.replace(" ", ""))
        self.words.append(key.split())
        self.titles.append(fold(re.sub(r"\(.*?\)|\[.*?\]", "", title)))
        self.artist_keys.append(fold(artist))
        return i

    def _find_or_add(self, artist, title):
        i = self.by_slug.get(slugify(artist, title))
        return self._add(artist, title) if i is None else i

    def set_library(self, songs, lyrics=None):
        """songs: library slug -> song.json. lyrics: slug -> its lines, so a remembered line finds the song."""
        for slug, s in songs.items():
            if slug not in self.by_slug:
                self._add(s.get("artist", ""), s.get("title", ""), id=slug)
        self.ready = set(songs)
        self.lyrics = {slug: [(fold(line), line) for line in lines] for slug, lines in (lyrics or {}).items()}

    # ---------------------------------------------------------------- reading

    def view(self, i, lyric=None):
        r = self.rows[i]
        ready = r["slug"] in self.ready
        out = {"id": r["id"], "artist": r["artist"], "title": r["title"], "year": r["year"], "duo": r["duo"],
               "status": "ready" if ready else "make", "slug": r["slug"] if ready else None}
        if lyric:
            out["lyric"] = lyric
        return out

    def get(self, id):
        i = self.by_id.get(id)
        return None if i is None else self.view(i)

    def _allowed(self, i, hide_explicit, langs):
        r = self.rows[i]
        return not (hide_explicit and r["explicit"]) and not (langs and r["langs"] and not r["langs"] & set(langs))

    def _popularity(self, i):
        return 1 - math.log1p(i) / math.log1p(len(self.rows))  # row order is the KaraFun popularity order

    def search(self, q, limit=8, hide_explicit=False, langs=None):
        qf = fold(q)
        tokens = qf.split()
        if not tokens:
            return []
        ok = lambda i: self._allowed(i, hide_explicit, langs)
        longest = max(tokens, key=len)  # cheap first pass: the longest typed word appears somewhere
        found = {i: self._score(i, tokens, qf) for i in [i for i, comp in enumerate(self.compact) if longest in comp]
                 if all(t in self.compact[i] for t in tokens) and ok(i)}
        hits = sorted(found, key=found.get, reverse=True)
        lyric = {}
        if len(tokens) >= 3:  # a remembered line of a song that's ready
            for slug, lines in self.lyrics.items():
                line = next((orig for folded, orig in lines if qf in folded), None)
                i = self.by_slug.get(slug)
                if line and i is not None and ok(i):
                    lyric[i] = line
        if len(hits) < limit:  # typos: the closest names or titles, popular ones first
            from rapidfuzz import fuzz, process
            near = {}
            for choices, cutoff in ((self.keys, 70), (self.titles, 75)):  # plain ratio: ~20 ms over 90k names, WRatio ~500
                for _, score, i in process.extract(qf, choices, scorer=fuzz.ratio, processor=None, limit=limit * 4, score_cutoff=cutoff):
                    if i not in found and ok(i):
                        near[i] = max(near.get(i, 0), score)
            hits += sorted(near, key=lambda i: -(near[i] / 10 + 3 * self._popularity(i)))
        order = list(lyric) + [i for i in hits if i not in lyric]
        return [self.view(i, lyric.get(i)) for i in order[:limit]]

    def _score(self, i, tokens, qf):
        words, s = self.words[i], 0.0
        for t in tokens:
            s += 3 if t in words else 2 if any(w.startswith(t) for w in words) else 1  # 1: inside a name like "acdc"
        title = self.titles[i]
        s += 6 if title == qf else 4 if title.startswith(qf) else 2 if qf in title else 0
        if self.artist_keys[i] == qf:
            s += 4
        # popularity outweighs an exact title: "atemlos" means Helene Fischer's hit, not a namesake nobody sings
        return s + 8 * self._popularity(i) + 2 * (self.rows[i]["slug"] in self.ready)

    def artists(self, q, limit=3):
        tokens = fold(q).split()
        if not tokens:
            return []
        found = {}
        for i, key in enumerate(self.artist_keys):
            if all(t in key for t in tokens) and all(any(w.startswith(t) for w in key.split()) for t in tokens):
                name = self.rows[i]["artist"]
                found[name] = found.get(name, 0) + 1  # first seen = most popular song: dicts keep that order
        return [{"artist": a, "count": n} for a, n in list(found.items())[:limit]]

    def prefetch(self, popular, skip=(), hide_explicit=False, langs=None):
        """What to make while the laptop is idle: songs this pub picked that aren't made, then more by the artists
        it picks, then the most popular songs in the languages it sings (the staff's languages, or English, until it has picked)."""
        picked = [self.by_id[c] for c in sorted(popular, key=lambda c: -popular[c]) if c in self.by_id]
        artists = {self.rows[i]["artist"] for i in picked}
        sung = set().union(*(self.rows[i]["langs"] for i in picked)) or set(langs or ["English"])
        fresh = lambda i: (self.rows[i]["slug"] not in self.ready and self.rows[i]["id"] not in skip
                           and self._allowed(i, hide_explicit, langs))
        everything = range(len(self.rows))  # in popularity order
        for pool, wanted in ((picked, lambda i: True),
                             (everything, lambda i: self.rows[i]["artist"] in artists),
                             (everything, lambda i: not self.rows[i]["langs"] or bool(self.rows[i]["langs"] & sung))):
            i = next((i for i in pool if wanted(i) and fresh(i)), None)
            if i is not None:
                return self.view(i)
        return None

    def by_artist(self, artist, hide_explicit=False, langs=None):
        return [self.view(i) for i, r in enumerate(self.rows) if r["artist"] == artist and self._allowed(i, hide_explicit, langs)]

    def shelf(self, name, page=0, size=30, hide_explicit=False, langs=None, popular=None):
        popular = popular or {}
        test = {
            "ready": lambda r: r["slug"] in self.ready,
            "here": lambda r: r["id"] in popular,
            "top": lambda r: True,
            "classics": lambda r: "classics" in r["sections"],
            "irish": lambda r: "irish" in r["sections"] or fold(r["artist"]) in self.irish,
            "german": lambda r: "German" in r["langs"] or "german" in r["sections"],
            "schlager": lambda r: "Schlager" in r["styles"],
            "80s": lambda r: 1980 <= (r["year"] or 0) <= 1989,
            "rock": lambda r: bool(r["styles"] & ROCK),
            "country": lambda r: "Country" in r["styles"],
            "duets": lambda r: r["duo"],
        }.get(name)
        if not test:
            return []
        idx = [i for i, r in enumerate(self.rows) if test(r) and self._allowed(i, hide_explicit, langs)]
        if name == "here":
            idx.sort(key=lambda i: -popular[self.rows[i]["id"]])
        return [self.view(i) for i in idx[page * size:(page + 1) * size]]
