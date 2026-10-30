from catalog import Catalog, fold

CSV = """Id;Title;Artist;Year;Duo;Explicit;Date Added;Styles;Languages
1;Bohemian Rhapsody;Queen;1975;0;0;01/01/2008;Rock;English
2;Highway to Hell;AC/DC;1979;0;0;01/01/2008;Hard Rock;English
3;Zombie;The Cranberries;1994;0;0;01/01/2008;Rock,Alternative;English
4;J'irai où tu iras;Céline Dion;1995;0;0;01/01/2008;French pop;French
5;Atemlos durch die Nacht;Helene Fischer;2013;0;0;01/01/2008;Schlager;German
6;Don't Stop Believin';Journey;1981;0;0;01/01/2008;Rock;English
7;Schrei nach Liebe;Die Ärzte;1993;0;1;01/01/2008;Punk/Grunge;German
8;Bohemian Rhapsody;Panic! at the Disco;2016;0;0;01/01/2008;Rock;English
9;Islands in the Stream;Dolly Parton & Kenny Rogers;1983;1;0;01/01/2008;Country,Duet;English
10;Dirty Old Town;The Pogues;1985;0;0;01/01/2008;Folk;English
"""
STARTER = "# Pub classics\nQueen - Bohemian Rhapsody\n# Irish\nThe Pogues - Fairytale of New York\n"


def mk(tmp_path, songs=None, lyrics=None):
    f = tmp_path / "karafun.csv"
    f.write_text(CSV, encoding="utf-8-sig")
    c = Catalog(f, STARTER)
    c.set_library(songs or {}, lyrics or {})
    return c


def first(c, q, **kw):
    hits = c.search(q, **kw)
    return f"{hits[0]['artist']} - {hits[0]['title']}" if hits else None


def test_fold_ignores_case_accents_and_spelling():
    assert fold("Céline Dion") == "celine dion"
    assert fold("Die Ärzte") == fold("die aerzte") == fold("Die Arzte")
    assert fold("Don't Stop") == fold("dont stop")
    assert fold("Dolly Parton & Kenny Rogers") == "dolly parton and kenny rogers"


def test_search_finds_what_guests_type(tmp_path):
    c = mk(tmp_path)
    assert first(c, "bohemian") == "Queen - Bohemian Rhapsody"          # the popular version first
    assert first(c, "bohemain rapsody") == "Queen - Bohemian Rhapsody"  # typos
    assert first(c, "acdc highway") == "AC/DC - Highway to Hell"
    assert first(c, "zombie cranb") == "The Cranberries - Zombie"       # any order, half-typed
    assert first(c, "celine") == "Céline Dion - J'irai où tu iras"
    assert first(c, "atemlos") == "Helene Fischer - Atemlos durch die Nacht"
    assert first(c, "dont stop") == "Journey - Don't Stop Believin'"
    assert first(c, "aerzte") == "Die Ärzte - Schrei nach Liebe"
    assert first(c, "panic bohemian") == "Panic! at the Disco - Bohemian Rhapsody"
    assert c.search("") == [] and c.search("zzzzqqq") == []


def test_filters_and_status(tmp_path):
    c = mk(tmp_path, songs={"queen-bohemian-rhapsody": {"artist": "Queen", "title": "Bohemian Rhapsody"},
                            "natu-rap-nada-leve": {"artist": "Natu Rap", "title": "Nada Leve"}})
    assert first(c, "aerzte", hide_explicit=True) is None
    assert first(c, "celine", langs={"English", "German"}) is None
    hit = c.search("bohemian")[0]
    assert hit["status"] == "ready" and hit["slug"] == "queen-bohemian-rhapsody"
    assert c.search("panic")[0]["status"] == "make"
    assert first(c, "nada leve") == "Natu Rap - Nada Leve"            # made songs that aren't in the list still show
    assert c.get(hit["id"])["title"] == "Bohemian Rhapsody" and c.get("nope") is None


def test_lyric_lines_find_their_song(tmp_path):
    c = mk(tmp_path, songs={"queen-bohemian-rhapsody": {"artist": "Queen", "title": "Bohemian Rhapsody"}},
           lyrics={"queen-bohemian-rhapsody": ["Is this the real life?", "Is this just fantasy?"]})
    hit = c.search("is this the real life")[0]
    assert hit["title"] == "Bohemian Rhapsody" and hit["lyric"] == "Is this the real life?"


def test_idle_laptop_makes_this_pubs_favourites(tmp_path):
    c = mk(tmp_path, songs={"helene-fischer-atemlos-durch-die-nacht": {"artist": "Helene Fischer", "title": "Atemlos durch die Nacht"}})
    title = lambda **kw: (c.prefetch(**kw) or {}).get("title")
    assert title(popular={"k3": 2, "k5": 5}) == "Zombie"                       # picked here, not made yet
    assert title(popular={"k5": 5}) == "Schrei nach Liebe"                     # made: next, more songs in German
    assert title(popular={"k5": 5}, hide_explicit=True) == "Fairytale of New York"  # starter songs have no language: allowed
    assert title(popular={}) == "Bohemian Rhapsody"                            # nobody picked yet: the top hits
    assert title(popular={}, skip={"k1", "k2"}) == "Zombie"                    # songs that failed are skipped


def test_artists_and_shelves(tmp_path):
    c = mk(tmp_path, songs={"the-cranberries-zombie": {"artist": "The Cranberries", "title": "Zombie"}})
    assert c.artists("bohem") == [] and c.artists("queen") == [{"artist": "Queen", "count": 1}]
    titles = lambda name, **kw: [r["title"] for r in c.shelf(name, **kw)]
    assert titles("ready") == ["Zombie"]
    assert titles("irish") == ["Dirty Old Town", "Fairytale of New York"]   # every song by the starter list's Irish artists
    assert titles("classics") == ["Bohemian Rhapsody"]
    assert titles("german") == ["Atemlos durch die Nacht", "Schrei nach Liebe"]
    assert titles("german", hide_explicit=True) == ["Atemlos durch die Nacht"]
    assert titles("80s") == ["Don't Stop Believin'", "Islands in the Stream", "Dirty Old Town"]
    assert titles("duets") == ["Islands in the Stream"]
    assert titles("here", popular={c.search("zombie")[0]["id"]: 3}) == ["Zombie"]
    assert titles("top", size=2) == ["Bohemian Rhapsody", "Highway to Hell"]
    assert titles("top", page=1, size=2) == ["Zombie", "J'irai où tu iras"]
    assert c.shelf("nonsense") == []
