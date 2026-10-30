from make_songs import *

def test_parse_song_list():
    txt = "# Pub classics\nQueen - Bohemian Rhapsody\n\n# Irish\nThe Pogues - Dirty Old Town\n# German\nNena - 99 Luftballons | neon80s\nAC/DC - T.N.T. - Live\n"
    s = parse_song_list(txt)
    assert s[0] == {"artist": "Queen", "title": "Bohemian Rhapsody", "hint": None, "lang": None}
    assert s[1]["hint"] == "celtic" and s[1]["lang"] is None
    assert s[2] == {"artist": "Nena", "title": "99 Luftballons", "hint": "neon80s", "lang": "de"}
    assert s[3] == {"artist": "AC/DC", "title": "T.N.T. - Live", "hint": "disco", "lang": "de"}

def test_parse_lrc_and_build_lines():
    lrc = parse_lrc("[00:01.50] Hello\n[00:04.00]\n[00:10.00][00:20.00] Again\n")
    assert lrc == [(1.5, "Hello"), (4.0, ""), (10.0, "Again"), (20.0, "Again")]
    lines = build_lines(lrc, 30.0)
    assert lines[0] == {"start": 1.5, "next": 4.0, "text": "Hello"}
    assert lines[-1] == {"start": 20.0, "next": 30.0, "text": "Again"}
    assert len(lines) == 3

def test_spread_words_caps_window_and_is_monotonic():
    w = spread_words(10.0, 40.0, "I am here")
    assert [x["w"] for x in w] == ["I", "am", "here"]
    assert w[0]["t"] == 10.0
    assert all(a["t"] < b["t"] for a, b in zip(w, w[1:]))
    assert w[-1]["t"] < 10.0 + 0.6 * 3 + 1.0

def test_spread_words_puts_words_where_the_voice_is():
    loud = [False] * 1000
    for i in range(int(12 / HOP), int(14 / HOP)):
        loud[i] = True                              # the singer is only audible from 12 s to 14 s
    w = spread_words(10.0, 20.0, "slow sad song", loud)
    assert [x["w"] for x in w] == ["slow", "sad", "song"]
    assert all(12.0 <= x["t"] < x["e"] <= 14.0 for x in w)
    assert all(a["e"] <= b["t"] + 0.001 for a, b in zip(w, w[1:]))


def lyric_lines(*starts_texts, end=100.0):
    return build_lines(list(starts_texts), end)


def test_line_offsets_follow_the_recording():
    lines = lyric_lines((10.0, "another head hangs lowly"), (20.0, "child is slowly taken"), (30.0, "and the violence caused such silence"),
                        (40.0, "who are we mistaken"), (50.0, "but you see it's not me"))
    heard = []
    for l in lines:  # this recording starts 12 s later than the lyric file says
        heard += [(w, l["start"] + 12 + k * 0.5, l["start"] + 12 + k * 0.5 + 0.4) for k, w in enumerate(l["text"].split())]
    heard[0] = ("another", 20.1, 20.5)              # the transcriber hears the first word 2 s early, after the long intro
    assert line_offsets(lines, heard) == [12.0] * 5
    assert line_offsets(lines, [("totally", 1, 2), ("different", 3, 4), ("song", 5, 6)]) is None


def test_line_offsets_dont_jump_to_another_chorus():
    chorus = ["turn around bright eyes", "every now and then", "i fall apart"]
    parts = [["once upon a time", "i was falling in love"], chorus, ["now i'm only falling apart", "there's nothing i can do"],
             chorus, ["a total eclipse of the heart", "and i need you now tonight"], chorus]
    lines = lyric_lines(*[(10.0 + 5 * i, text) for i, text in enumerate(t for p in parts for t in p)], end=150.0)
    heard = []
    for i, l in enumerate(lines):  # sung 2 s after the lyric file; the first chorus and one word per verse line misheard
        words = l["text"].split()
        if 2 <= i <= 4:
            words = ["la"] * len(words)
        elif l["text"] not in chorus:
            words[-1] = "mm"
        heard += [(w, l["start"] + 2 + k * 0.4, l["start"] + 2.3 + k * 0.4) for k, w in enumerate(words)]
    assert line_offsets(lines, heard) == [2.0] * len(lines)


def sung(lines, shift=0.0):
    """What the transcriber hears when every line is sung `shift` seconds after its time in the lyric file."""
    return [(w, l["start"] + shift + k * 0.4, l["start"] + shift + k * 0.4 + 0.3) for l in lines for k, w in enumerate(l["text"].split())]


def test_vote_offsets_follow_a_shift_through_repeated_lines():
    lines = lyric_lines((10.0, "turn around"), (20.0, "every now and then"), (30.0, "turn around"), (40.0, "every now and then"), (50.0, "bright eyes"))
    assert vote_offsets(lines, sung(lines, 3.0)) == [3.0] * 5      # each "turn around" takes the nearest one sung, not the first
    assert vote_offsets(lines, [("totally", 1, 2), ("different", 3, 4)]) is None


def test_best_fit_picks_the_lyric_file_that_fits_the_recording():
    edit = lyric_lines((10.0, "we were young once"), (20.0, "turn around bright eyes"), (30.0, "every now and then"), (40.0, "i fall apart tonight"))
    album = lyric_lines((10.0, "we were young once"), (20.0, "a long extra verse here"), (30.0, "another extra line now"),
                        (50.0, "turn around bright eyes"), (60.0, "every now and then"), (70.0, "i fall apart tonight"))
    lines, offsets = best_fit([album, edit], sung(edit, 1.0))     # the lyrics site's first upload is the long album version
    assert lines is edit and offsets == [1.0] * 4
    assert heard_at(edit, sung(edit, 1.0), offsets) == 4 and heard_at(edit, sung(edit, 1.0), [0.0] * 4) == 4
    assert heard_at(edit, sung(edit, 1.0), [5.0] * 4) == 0


def test_windows_never_overlap_and_stay_in_the_song():
    lines = lyric_lines((10.0, "a b"), (12.0, "c d"), (200.0, "e f"), (210.0, "g h"), end=215.0)
    wins = windows(lines, [3.0, -1.5, 9.0, 9.0], 215.0)   # offsets that disagree, and a last line pushed past the end
    assert [w["text"] for w in wins] == ["a b", "c d", "e f", "g h"]
    assert all(w["start"] < w["end"] for w in wins)
    assert all(a["end"] <= b["start"] for a, b in zip(wins, wins[1:]))
    assert wins[0]["start"] == 12.7 and wins[2]["end"] <= wins[2]["start"] + 2.0 * 2 + 4


def test_merge_alignment_keeps_confident_lines_and_falls_back_per_line():
    lines = lyric_lines((1.0, "a b"), (5.0, "c d"), end=9.0)
    wins = windows(lines, [0.0, 0.0], 9.0)
    aligned = [[{"w": "a", "t": 1.2, "e": 1.7, "p": 0.9}, {"w": "b", "t": 1.8, "e": 2.6, "p": 0.8}],
               [{"w": "c", "t": 4.8, "e": 4.8, "p": 0.1}, {"w": "d", "t": 4.8, "e": 4.8, "p": 0.0}]]  # collapsed: not trusted
    out, score = merge_alignment(lines, wins, aligned)
    assert out[0]["words"] == [{"w": "a", "t": 1.2, "e": 1.7}, {"w": "b", "t": 1.8, "e": 2.6}]
    assert out[0]["start"] == 1.2 and out[0]["end"] == 2.6 and out[0]["lrc"] == 1.0
    assert out[1]["words"][0]["t"] == wins[1]["start"] and out[1]["lrc"] == 5.0   # spread fallback inside its window
    assert score == 0.5
    assert merge_alignment(lines, wins, None)[1] == 0.0


def test_word_ends_are_trimmed_to_the_voice():
    loud = [False] * 500
    for i in range(int(1.0 / HOP), int(1.5 / HOP)):
        loud[i] = True
    lines = lyric_lines((1.0, "oh"), end=9.0)
    out, _ = merge_alignment(lines, windows(lines, [0.0], 9.0), [[{"w": "oh", "t": 1.0, "e": 6.0, "p": 0.9}]], loud)
    assert out[0]["words"][0]["e"] == 1.5           # the voice stops at 1.5 s, so the wipe does too

def test_pick_pair_by_duration():
    lrc = [{"duration": 168.0, "syncedLyrics": "x"}, {"duration": 199.0, "syncedLyrics": "y"}, {"duration": 200.0, "syncedLyrics": None}]
    yt = [{"id": "A", "duration": 201, "title": "a"}, {"id": "B", "duration": 198, "title": "b"}]
    assert pick_pair(lrc, yt) == (lrc[1], yt[1])
    assert pick_pair(lrc, [{"id": "C", "duration": 300, "title": "c"}]) is None
    # every video once, closest first: a video whose singing doesn't match the lyrics can be swapped for the next
    assert [y["id"] for _, y in pick_pairs(lrc, yt)] == ["B", "A"]


def test_pick_pairs_wants_a_video_long_enough_for_the_lyrics():
    album = {"duration": 271.0, "syncedLyrics": "[00:15.00] Turn around\n[06:14.00] Turn around bright eyes\n[06:20.00]"}  # tagged with the single's length
    edit, full = {"id": "edit", "duration": 271, "title": "a"}, {"id": "album", "duration": 418, "title": "b"}
    assert [y["id"] for _, y in pick_pairs([album], [edit, full])] == ["album"]
    assert pick_pairs([album], [edit, {"id": "far", "duration": 600, "title": "c"}]) == []

def test_remake_keeps_whichever_recording_times_better(tmp_path, monkeypatch):
    import make_songs
    lib, work = tmp_path / "library", tmp_path / "work"
    for slug, score in (("a-worse", 0.4), ("b-better", 0.1)):
        (lib / slug).mkdir(parents=True)
        (lib / slug / "song.json").write_text(json.dumps({"artist": slug[0], "title": slug[2:], "duration": 200.0, "theme": "rock",
                                                          "sync": {"v": 2, "aligned": score, "nudge": 0.3}}))
    tried = []

    def fake_make(req, library, work_, model, overlap, skip, tries, good_enough):
        tried.append((skip({"id": "x", "duration": 200}), skip({"id": "y", "duration": 230}), tries, good_enough))
        out = library / slugify(req["artist"], req["title"])
        out.mkdir(parents=True)
        (out / "song.json").write_text(json.dumps({"duration": 230.0, "lang": "en", "theme": "pop", "video": "y", "sync": {"v": 2, "aligned": 0.3}}))
        return "ok"
    monkeypatch.setattr(make_songs, "make_song", fake_make)
    assert remake(["a-worse", "b-better"], lib, work, None, 4) == 1
    assert tried[0] == (True, False, 3, 0.8)                        # the same recording isn't tried again
    kept = json.loads((lib / "a-worse" / "song.json").read_text())
    assert kept["sync"]["aligned"] == 0.4 and kept["duration"] == 200.0
    swapped = json.loads((lib / "b-better" / "song.json").read_text())
    assert swapped["sync"] == {"v": 2, "aligned": 0.3} and swapped["duration"] == 230.0 and swapped["video"] == "y"
    assert swapped["theme"] == "rock"                                # staff's look stays; the old nudge was for the old recording
    assert (work / "replaced" / "b-better" / "song.json").exists()


def test_usable_video():
    assert usable_video("Queen - Bohemian Rhapsody (Official Audio)", "Bohemian Rhapsody")
    assert not usable_video("Bohemian Rhapsody KARAOKE", "Bohemian Rhapsody")
    assert usable_video("Live and Let Die (Remastered)", "Live and Let Die")

def test_pick_itunes_earliest_year():
    r = [{"artistName": "Queen", "primaryGenreName": "Rock", "releaseDate": "2006-01-01T00:00:00Z", "artworkUrl100": "http://x/100x100bb.jpg"},
         {"artistName": "Queen", "primaryGenreName": "Rock", "releaseDate": "1975-10-31T00:00:00Z", "artworkUrl100": "http://y/100x100bb.jpg"},
         {"artistName": "Other", "primaryGenreName": "Pop", "releaseDate": "1960-01-01T00:00:00Z", "artworkUrl100": "z"}]
    assert pick_itunes(r, "queen") == {"genre": "Rock", "year": 1975, "cover": "http://x/600x600bb.jpg"}
    assert pick_itunes([], "queen") is None

def test_guess_lang_and_theme():
    assert guess_lang("Atemlos durch die Nacht, ich und du, das ist nicht") == "de"
    assert guess_lang("Is this the real life, is this just fantasy and you") == "en"
    assert guess_lang("Je n'ai qu'une philosophie, être acceptée comme je suis, malgré tout ce qu'on me dit") == "fr"
    assert guess_lang("Sarà perché ti amo, e vola via, che confusione, sarà perché ti amo") == "it"
    assert guess_lang("") == "en"
    assert pick_theme("celtic", "Rock", 1985, "en") == "celtic"
    assert pick_theme(None, "Hard Rock", 1985, "en") == "rock"
    assert pick_theme(None, "Pop", 1984, "en") == "neon80s"
    assert pick_theme(None, "Schlager", 2013, "de") == "disco"
    assert pick_theme(None, "Singer/Songwriter", 2005, "en") == "ballad"
    assert pick_theme(None, "Pop", 2017, "en") == "pop"
    assert pick_theme(None, "Comedy", None, "en") == "cover"
    assert pick_theme(None, "Alternative", 1988, "en", tags=["folk punk"], country="IE") == "celtic"
    assert pick_theme(None, "Pop", 2014, "de", tags=["schlager", "german"], country="DE") == "disco"
    assert pick_theme(None, "Pop", 1983, "de", tags=["neue deutsche welle"]) == "neon80s"

def test_slugify():
    assert slugify("Helene Fischer", "Atemlos durch die Nacht") == "helene-fischer-atemlos-durch-die-nacht"
    assert slugify("Die Ärzte", "Schrei nach Liebe!") == "die-aerzte-schrei-nach-liebe"
    assert slugify("AC/DC", "T.N.T.") == "ac-dc-t-n-t"


def test_unknown_theme_hint_is_ignored():
    assert pick_theme("toString", "Rock", 1995, "en") == "rock"
    assert parse_song_list("# Wishes\nAbba - Waterloo | __proto__\n")[0]["hint"] is None


def test_pick_wish_rejects_lookalikes():
    c = lambda a, t: {"artistName": a, "trackName": t}
    natu = [c("Natu Rap, EoCROSSS", "Nada Leve (feat. Dave Natu, Jooj Natu & Oli Natu)"), c("Arjun Tomar", "Mujhe Door Natu Jane De")]
    assert pick_wish("Natu natu", natu) is None
    assert pick_wish("naatu naatu", natu + [c("Rahul Sipligunj", "Naatu Naatu")])["trackName"] == "Naatu Naatu"
    assert pick_wish("africa toto", [c("Toto", "Africa"), c("Weezer", "Africa")])["artistName"] == "Toto"
    assert pick_wish("Skandal", [c("Spider Murphy Gang", "Skandal im Sperrbezirk")]) is not None
    assert pick_wish("bohemian rhapsody", [c("Queen", "Bohemian Rhapsody - Remastered 2011")]) is not None
    assert pick_wish("anything", []) is None


def test_serve_always_answers(monkeypatch, capsys, tmp_path):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO("#1 Crush\n"))  # reads as a section header: nothing to make
    serve(tmp_path, tmp_path, None, 4)
    assert capsys.readouterr().out.strip().startswith("FAIL")       # the app waits for an answer, so there must be one


def test_serve_retimes_only_song_folders(monkeypatch, capsys, tmp_path):
    import io
    (tmp_path / "a-b").mkdir()
    monkeypatch.setattr("make_songs.retime", lambda slugs, library, model: 1)
    monkeypatch.setattr("sys.stdin", io.StringIO("RETIME ../a-b\nRETIME C:/x\nRETIME a-b\n"))
    serve(tmp_path, tmp_path, None, 4)
    fail = "FAIL error: could not re-time"
    assert capsys.readouterr().out.splitlines() == [fail, fail, "SLUG a-b"]


def test_prefetch_without_the_song_list_says_where_to_get_it(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr("make_songs.ROOT", tmp_path)
    prefetch(1, tmp_path, tmp_path, None, 4)
    assert KARAFUN_LIST in capsys.readouterr().out
