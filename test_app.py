from app import Party, QueueError, clean_name
import pytest

SONGS = {s: {"help_vocals": 0.25} for s in ["s1", "s2", "s3", "s4"]}

def mk(**kw):
    t = iter(range(1000))
    return Party(dict(SONGS), now=lambda: next(t), **kw)

def test_fair_order_and_upcoming():
    p = mk()
    p.add("Anna", "d1", "s1"); p.add("Anna", "d1", "s2"); p.add("Ben", "d2", "s3")
    assert [e["song_id"] for e in p.upcoming()] == ["s1", "s3", "s2"]
    order = []
    while (e := p.next()):
        order.append(e["song_id"]); p.done(e["id"])
    assert order == ["s1", "s3", "s2"]

def test_limit_counts_queued_only_and_names_case_insensitive():
    p = mk()
    p.add("Anna", "d1", "s1"); p.add("anna ", "d1", "s2")
    with pytest.raises(QueueError, match="limit"):
        p.add("ANNA", "d1", "s3")
    p.done(p.next()["id"])
    p.add("Anna", "d1", "s3")

def test_same_song_twice_rejected():
    p = mk(); p.add("Anna", "d1", "s1")
    with pytest.raises(QueueError, match="duplicate"):
        p.add("Anna", "d1", "s1")

def test_unknown_song_and_bad_name():
    p = mk()
    with pytest.raises(QueueError, match="unknown_song"): p.add("Anna", "d1", "nope")
    with pytest.raises(QueueError, match="bad_name"): p.add("  \x07 ", "d1", "s1")
    assert clean_name("  <b>" + "x" * 40) == ("<b>" + "x" * 40)[:24]

def test_remove_own_only():
    p = mk(); e = p.add("Anna", "d1", "s1")
    with pytest.raises(QueueError, match="forbidden"): p.remove(e["id"], device="d2")
    p.remove(e["id"], device="d1"); assert p.queue == []
    e = p.add("Anna", "d1", "s1"); p.remove(e["id"], staff=True); assert p.queue == []

def test_next_returns_current_until_done():
    p = mk(); p.add("Anna", "d1", "s1"); p.add("Ben", "d2", "s2")
    a = p.next(); assert p.next()["id"] == a["id"]

def test_done_is_idempotent_by_id():
    p = mk(); p.add("Anna", "d1", "s1"); p.add("Ben", "d2", "s2")
    a = p.next()
    assert p.done(a["id"]) is True
    b = p.next()
    assert p.done(a["id"]) is False and p.now_playing["id"] == b["id"]

def test_next_skips_missing_songs():
    p = mk(); p.add("Anna", "d1", "s1"); p.add("Ben", "d2", "s2")
    del p.songs["s1"]
    assert p.next()["song_id"] == "s2" and p.queue == []

def test_wish_plays_from_youtube_until_made():
    p = mk()
    a = p.add("Anna", "d1", "", wish="X - Y", yt=["v1"])
    p.add("Ben", "d2", "", wish="X - Y")
    p.add("Cara", "d3", "", wish="Gone - Song")
    with pytest.raises(QueueError, match="duplicate"): p.add("Anna", "d1", "", wish="X - Y")
    p.unmakeable("Gone - Song")  # no video, can't be made: dropped
    assert [e["name"] for e in p.queue] == ["Anna", "Ben"]
    p.songs["x-y"] = {}
    p.made("X - Y", "x-y")
    assert {e["song_id"] for e in p.queue} == {"x-y"}
    p.unmakeable("X - Y")  # made entries are never dropped
    assert p.next()["id"] == a["id"] and len(p.queue) == 1

def test_next_ready_singer_goes_first_and_the_waiting_one_keeps_their_place():
    p = mk()
    anna = p.add("Anna", "d1", "", wish="X - Y", catalog="k1")   # being made
    p.add("Ben", "d2", "s2")
    assert p.next()["name"] == "Ben"
    p.done(p.now_playing["id"])
    p.add("Ben", "d2", "s3")
    assert [e["name"] for e in p.upcoming()] == ["Anna", "Ben"]   # Anna hasn't sung: still first in line
    p.songs["x-y"] = {}
    p.made("X - Y", "x-y")
    assert p.next()["id"] == anna["id"]


def test_songs_being_made_are_waited_for_never_swapped_for_youtube():
    clock = [0.0]
    p = Party(dict(SONGS), now=lambda: clock[0], can_make=True)
    p.add("Anna", "d1", "", wish="X - Y", yt=["v1"])
    clock[0] = 3600.0
    assert p.next() is None                                       # however long it takes: the real song, not YouTube
    p.unmakeable("X - Y")                                         # only when it can't be made does the video play
    assert p.next()["name"] == "Anna"


def test_without_a_song_maker_a_wish_plays_as_video_after_its_own_wait():
    clock = [0.0]
    p = Party(dict(SONGS), now=lambda: clock[0])                  # no song maker on this laptop
    p.add("Anna", "d1", "", wish="X - Y", yt=["v1"])
    clock[0] = 60.0
    p.add("Ben", "d2", "", wish="Z - W", yt=["v2"])
    assert p.next() is None
    clock[0] = 91.0
    assert p.next()["name"] == "Anna"                             # 90 s since Anna picked it
    p.done(p.now_playing["id"])
    clock[0] = 100.0
    assert p.next() is None                                       # Ben picked his 40 s ago: the earlier wait doesn't count
    clock[0] = 151.0
    assert p.next()["name"] == "Ben"


def test_video_only_pick_is_ready_at_once():
    p = mk()
    p.add("Anna", "d1", "", wish="No - Lyrics", yt=["v1"], video=True)
    assert p.next()["name"] == "Anna"


def test_pin_goes_first():
    p = mk(); p.add("Anna", "d1", "s1"); e = p.add("Ben", "d2", "s2")
    p.pin(e["id"]); assert p.upcoming()[0]["id"] == e["id"]

def test_save_load_and_new_night(tmp_path):
    f = tmp_path / "state.json"
    clock = [1000.0]
    p = Party(dict(SONGS), path=f, now=lambda: clock[0]); p.add("Anna", "d1", "s1"); p.next()
    q = Party.load(f, dict(SONGS), 2, now=lambda: clock[0] + 60)
    assert q.now_playing["song_id"] == "s1" and q.turns == {"anna": 1}
    r = Party.load(f, dict(SONGS), 2, now=lambda: clock[0] + 13 * 3600)
    assert r.queue == [] and r.turns == {} and r.now_playing is None


# ---------------------------------------------------------------- API

import json
from app import create_app


@pytest.fixture
def client(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "9999", "port": 5000}))
    (tmp_path / "static").mkdir()
    for page in ("guest", "admin", "tv", "print"):
        (tmp_path / "static" / f"{page}.html").write_text(page)
    song = tmp_path / "library" / "a-b"
    song.mkdir(parents=True)
    (song / "song.json").write_text(json.dumps({"artist": "A", "title": "B", "year": 1990, "theme": "pop", "help_vocals": 0.25}))
    return create_app(tmp_path).test_client()


def ready_shelf(client):
    return [s["slug"] for s in client.get("/api/browse?shelf=ready").json["songs"]]


def test_api_flow(client):
    assert ready_shelf(client) == ["a-b"]
    r = client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    assert r.status_code == 200
    st = client.get("/api/state?device=d1").json
    assert st["queue"][0]["mine"] is True and "device" not in st["queue"][0]
    e = client.post("/api/next", json={}).json["entry"]
    assert client.get("/api/state").json["now_playing"]["title"] == "B"
    assert client.post("/api/admin/skip", json={"id": e["id"]}, headers={"X-Pin": "0000"}).status_code == 403
    assert client.post("/api/admin/skip", json={"id": e["id"]}, headers={"X-Pin": "9999"}).status_code == 200
    assert client.get("/api/state").json["now_playing"] is None


def test_wish_and_library_file_whitelist(client, tmp_path, monkeypatch):
    import app
    monkeypatch.setattr(app, "karaoke_videos", lambda text: ["vid1", "vid2"])
    r = client.post("/api/wish", json={"text": "Abba – Waterloo\nhack", "name": "Anna", "device": "d1"})
    assert r.status_code == 200 and r.json["song"]["title"] == "Abba - Waterloo hack" and r.json["mine"]
    assert client.post("/api/wish", json={"text": "  ", "name": "Anna"}).status_code == 400
    assert client.post("/api/wish", json={"text": "x", "name": " "}).json["error"] == "bad_name"
    assert (tmp_path / "wishes.txt").read_text(encoding="utf-8") == "Abba - Waterloo hack\n"
    assert client.post("/api/next", json={}).json["entry"] is None           # not made yet: the stage waits a little first
    client.post("/api/admin/settings", json={"max_wait_seconds": 0}, headers={"X-Pin": "9999"})
    e = client.post("/api/next", json={}).json["entry"]
    assert e["song_id"] == "" and e["yt"] == ["vid1", "vid2"] and e["title"] == "Abba - Waterloo hack"
    assert client.get("/library/a-b/song.json").status_code == 200
    assert client.get("/library/a-b/../../settings.json").status_code == 404


def test_songs_made_while_running_show_up(client, tmp_path):
    assert ready_shelf(client) == ["a-b"]
    (tmp_path / "library" / "c-d").mkdir()
    (tmp_path / "library" / "c-d" / "song.json").write_text(json.dumps({"artist": "C", "title": "D"}))
    assert ready_shelf(client) == ["a-b", "c-d"]
    assert client.get("/api/search?q=d").json["songs"][0]["status"] == "ready"
    assert client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "c-d"}).status_code == 200


@pytest.fixture
def pub(tmp_path, monkeypatch):
    """The client with a song list: A - B is made, the others aren't."""
    (tmp_path / "library").mkdir(exist_ok=True)
    (tmp_path / "library" / "karafuncatalog.csv").write_text(
        "Id;Title;Artist;Year;Duo;Explicit;Date Added;Styles;Languages\n1;B;A;1990;0;0;x;Pop;English\n"
        "2;Zombie;The Cranberries;1994;0;0;x;Rock;English\n3;No Lyrics;Nobody;2000;0;0;x;Pop;English\n", encoding="utf-8")
    import app
    lyrics = {"Zombie": True, "No Lyrics": False}
    monkeypatch.setattr(app, "has_synced_lyrics", lambda artist, title: lyrics.get(title))
    monkeypatch.setattr(app, "karaoke_videos", lambda text: ["v1"])
    return tmp_path


def test_guests_pick_from_the_whole_list(pub, client):
    pick = lambda name, cid, **kw: client.post("/api/queue", json={"name": name, "device": name, "catalog_id": cid, **kw})
    assert pick("Anna", "k1").json["song_id"] == "a-b"                      # made already: plays from the library
    r = pick("Ben", "k2")                                                   # not made: checked, queued, made in time
    assert r.status_code == 200 and r.json["status"] == "waiting" and r.json["song"]["title"] == "Zombie"
    assert pick("Cara", "k3").json["error"] == "no_lyrics"                  # no timed lyrics anywhere
    assert pick("Cara", "k3", video=True).json["status"] == "video"         # ...but the karaoke video will do
    assert client.get("/api/search?q=no lyrics").json["songs"][0]["status"] == "video"
    assert pick("Dan", "nope").json["error"] == "unknown_song"
    import app
    app.has_synced_lyrics = lambda artist, title: None                      # monkeypatch undoes this after the test
    assert pick("Dan", "k2").json["error"] == "offline"
    st = client.get("/api/state").json
    assert [(e["name"], e["status"]) for e in st["queue"]] == [("Anna", "ready"), ("Ben", "waiting"), ("Cara", "video")]
    assert json.loads((pub / "history.json").read_text(encoding="utf-8")).keys() == {"k1", "k2", "k3"}
    assert [s["title"] for s in client.get("/api/browse?shelf=here").json["songs"]] == ["B", "Zombie", "No Lyrics"]


def test_staff_song_care(pub, client):
    lib = pub / "library"
    (lib / "c-d").mkdir()
    (lib / "c-d" / "song.json").write_text(json.dumps({"artist": "C", "title": "D", "sync": {"v": 2, "aligned": 0.9}}))
    client.post("/api/queue", json={"name": "Cara", "device": "d3", "catalog_id": "k3", "video": True})
    get = lambda: client.get("/api/admin/songs", headers=PIN).json
    assert client.get("/api/admin/songs").status_code == 403
    songs = get()
    assert [s["slug"] for s in songs["weak"]] == ["a-b"]                   # never re-timed: the timing may be guessed
    assert [(s["id"], s["why"]) for s in songs["failed"]] == [("k3", "no_lyrics")]
    assert songs["disk_gb"] >= 0 and songs["next"] == []
    assert client.post("/api/admin/retime", json={"slug": "a-b"}, headers=PIN).status_code == 200
    assert get()["next"] == ["Re-time: A - B"]
    assert client.post("/api/admin/retime", json={"slug": "../x"}, headers=PIN).json["error"] == "not_found"
    assert client.post("/api/admin/retry", json={"id": "k3"}, headers=PIN).status_code == 200
    assert get()["failed"] == []
    assert client.post("/api/admin/delete_song", json={"slug": "c-d"}, headers=PIN).status_code == 200
    assert not (lib / "c-d").exists() and ready_shelf(client) == ["a-b"]
    assert client.post("/api/admin/delete_song", json={"slug": "karafuncatalog.csv"}, headers=PIN).json["error"] == "not_found"


def test_same_song_twice_even_after_it_was_made():
    p = mk()
    p.add("Anna", "d1", "", wish="X - Y")
    p.songs["x-y"] = {}
    p.made("X - Y", "x-y")
    with pytest.raises(QueueError, match="duplicate"):
        p.add("Anna", "d1", "x-y")


def test_refused_wishes_answer_before_the_slow_search(client, tmp_path, monkeypatch):
    import app
    def no_search(text):
        raise AssertionError("searched YouTube for a wish that was refused anyway")
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    client.post("/api/admin/settings", json={"songs_per_singer": 1}, headers=PIN)
    monkeypatch.setattr(app, "karaoke_videos", no_search)
    assert client.post("/api/wish", json={"text": "X - Y", "name": "Anna", "device": "d1"}).json["error"] == "limit"
    assert not (tmp_path / "wishes.txt").exists()


FAKE_MAKER = r'''
import json, pathlib, re, sys
for line in sys.stdin:
    t = line.strip()
    with open("received.txt", "a") as f:
        f.write(t + "\n")
    if t.startswith("Good"):
        slug = re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")
        (pathlib.Path("library") / slug).mkdir(parents=True, exist_ok=True)
        (pathlib.Path("library") / slug / "song.json").write_text(json.dumps({"artist": "Good", "title": "Song"}))
        print("STAGE separate 40", flush=True)
        print("SLUG " + slug, flush=True)
    elif t.startswith("Flaky"):
        print("FAIL error ConnectionError: LRCLIB not answering", flush=True)
    elif t.startswith("Slow"):  # a long background song
        import time
        time.sleep(20)
        print("FAIL no synced lyrics on LRCLIB", flush=True)
    else:
        print("FAIL no synced lyrics on LRCLIB", flush=True)
'''


def test_song_maker_retries_blips_and_gives_up_on_hopeless_songs(tmp_path, monkeypatch):
    import subprocess, sys, time as clock
    import app
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "9999", "auto_download": False}))
    (tmp_path / "make_songs.py").write_text(FAKE_MAKER)
    (tmp_path / ".venv-maker" / "Scripts").mkdir(parents=True)
    (tmp_path / ".venv-maker" / "Scripts" / "python.exe").write_text("")  # stands in; the real interpreter runs it
    real = subprocess.Popen
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kw: real(  # only the song maker's launch is redirected
        [sys.executable, *args[1:]] if str(args[0]).endswith("python.exe") else args, **kw))
    monkeypatch.setattr(app, "karaoke_videos", lambda text: [])
    c = app.create_app(tmp_path).test_client()
    for name, wish in (("Anna", "Good - Song"), ("Ben", "Flaky - Song"), ("Cara", "NoLyrics - Song")):
        assert c.post("/api/wish", json={"text": wish, "name": name, "device": name}).status_code == 200
    deadline = clock.time() + 20
    while clock.time() < deadline:
        q = c.get("/api/state").json["queue"]
        if [e["name"] for e in q] == ["Anna"] and q[0]["status"] == "ready":
            break
        clock.sleep(0.2)
    assert [(e["name"], e["status"]) for e in q] == [("Anna", "ready")]   # Ben and Cara had no video to fall back on
    sent = (tmp_path / "received.txt").read_text().split("\n")
    assert sent.count("Flaky - Song") == 2                                 # a network blip gets one more try
    assert sent.count("NoLyrics - Song") == 1                              # no lyrics won't change tonight
    assert c.post("/api/wish", json={"text": "NoLyrics - Song", "name": "Cara", "device": "Cara"}).json["error"] == "no_video"


def test_a_guest_pick_interrupts_a_background_song(tmp_path, monkeypatch):
    import subprocess, sys, time as clock
    import app
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "9999", "auto_download": True}))
    (tmp_path / "library").mkdir()
    (tmp_path / "library" / "karafuncatalog.csv").write_text(
        "Id;Title;Artist;Year;Duo;Explicit;Date Added;Styles;Languages\n1;Song;Slow;2000;0;0;x;Pop;English\n", encoding="utf-8")
    (tmp_path / "make_songs.py").write_text(FAKE_MAKER)
    (tmp_path / ".venv-maker" / "Scripts").mkdir(parents=True)
    (tmp_path / ".venv-maker" / "Scripts" / "python.exe").write_text("")
    real = subprocess.Popen
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kw: real(  # only the song maker's launch is redirected
        [sys.executable, *args[1:]] if str(args[0]).endswith("python.exe") else args, **kw))
    monkeypatch.setattr(app, "karaoke_videos", lambda text: [])
    c = app.create_app(tmp_path).test_client()
    wait = lambda done, secs: next((True for _ in range(int(secs * 5)) if done() or clock.sleep(0.2)), done())
    assert wait(lambda: c.get("/api/state").json["maker"].get("wish") == "Slow - Song", 10)  # idle: a background song
    clock.sleep(0.5)
    t0 = clock.time()
    c.post("/api/wish", json={"text": "Good - Song", "name": "Anna", "device": "a"})
    assert wait(lambda: c.get("/api/state").json["queue"][0]["status"] == "ready", 15)
    assert clock.time() - t0 < 10                                           # not 20 s behind the background song


def test_the_maker_works_in_singing_order(pub):
    from app import next_to_make
    p = mk()
    p.add("Anna", "d1", "", wish="X - Y")
    p.turns["anna"] = 1                                                     # Anna has sung tonight, Ben hasn't
    p.add("Ben", "d2", "", wish="Z - W")
    p.add("Cara", "d3", "", wish="V - V", yt=["v"], video=True)             # videos aren't made
    assert next_to_make(p)["wish"] == "Z - W"
    assert next_to_make(p, skip={"Z - W"})["wish"] == "X - Y"


def test_queue_errors_have_codes(client):
    ok = {"name": "Anna", "device": "d1", "song_id": "a-b"}
    e = client.post("/api/queue", json=ok).json
    r = client.post("/api/queue", json=ok)
    assert r.status_code == 400 and r.json["error"] == "duplicate"
    assert client.delete(f"/api/queue/{e['id']}?device=d2").status_code == 403
    assert client.delete(f"/api/queue/{e['id']}?device=d1").status_code == 200


def test_help_vocals_saved_to_playing_song(client, tmp_path):
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    client.post("/api/next", json={})
    assert client.post("/api/admin/help_vocals", json={"level": 0.6}, headers={"X-Pin": "9999"}).status_code == 200
    assert client.get("/api/state").json["help_vocals"] == 0.6
    assert json.loads((tmp_path / "library" / "a-b" / "song.json").read_text())["help_vocals"] == 0.6


PIN = {"X-Pin": "9999"}


def test_staff_screen_settings_are_checked_saved_and_shown(client, tmp_path):
    assert client.get("/api/state").json["display"]["layout"] == "auto"
    ok = {"display": {"layout": "scroll", "size": "XL", "screen_delay_ms": 120}, "songs_per_singer": 3}
    assert client.post("/api/admin/settings", json=ok).status_code == 403          # no PIN
    assert client.post("/api/admin/settings", json=ok, headers=PIN).status_code == 200
    st = client.get("/api/state").json
    assert st["display"]["layout"] == "scroll" and st["display"]["highlight"] == "auto" and st["songs_per_singer"] == 3
    saved = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert saved["display"]["screen_delay_ms"] == 120 and saved["pin"] == "9999"
    for bad in ({"display": {"layout": "sideways"}}, {"pin": "0000"}, {"display": {"screen_delay_ms": True}},
                {"songs_per_singer": 99}, {"display": {"evil": 1}}, ["not", "a", "dict"]):
        assert client.post("/api/admin/settings", json=bad, headers=PIN).json["error"] == "bad_setting"
    assert client.get("/api/state").json["display"]["layout"] == "scroll"       # a refused change leaves everything as it was


def test_lyrics_nudge_is_kept_for_the_song(client, tmp_path):
    assert client.post("/api/admin/nudge", json={"delta": 0.1}, headers=PIN).status_code == 400  # nothing playing
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    client.post("/api/next", json={})
    client.post("/api/admin/nudge", json={"delta": 0.1}, headers=PIN)
    assert client.post("/api/admin/nudge", json={"delta": 0.1}, headers=PIN).json["nudge"] == 0.2
    assert client.get("/api/state").json["nudge"] == 0.2
    assert json.loads((tmp_path / "library" / "a-b" / "song.json").read_text(encoding="utf-8"))["sync"] == {"nudge": 0.2}
    client.post("/api/admin/synctest", json={"on": True}, headers=PIN)
    assert client.get("/api/state").json["synctest"] is True


def test_staff_sliders_on_a_youtube_wish_dont_crash(client, monkeypatch):
    import app
    monkeypatch.setattr(app, "karaoke_videos", lambda text: ["vid1"])
    client.post("/api/wish", json={"text": "Abba - Waterloo", "name": "Anna", "device": "d1"})
    client.post("/api/next", json={})
    assert client.post("/api/admin/help_vocals", json={"level": 0.5}, headers=PIN).status_code == 200


def test_now_playing_marks_my_song(client):
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    client.post("/api/next", json={})
    assert client.get("/api/state?device=d1").json["now_playing"]["mine"] is True
    assert client.get("/api/state?device=d2").json["now_playing"]["mine"] is False


def test_settings_with_byte_order_mark_load(tmp_path):
    # Notepad and PowerShell may save settings.json with a UTF-8 BOM
    (tmp_path / "settings.json").write_bytes(b'\xef\xbb\xbf{"pin": "4321"}')
    (tmp_path / "static").mkdir()
    assert create_app(tmp_path).config["settings"]["pin"] == "4321"


# ---------------------------------------------------------------- final review fixes

from app import bind_exclusive


def test_second_server_on_same_port_is_refused():
    import socket
    first = bind_exclusive(0)  # 0 = any free port
    port = first.getsockname()[1]
    second = socket.socket()
    second.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # what waitress does on its own bind
    try:
        with pytest.raises(OSError):
            second.bind(("0.0.0.0", port))
    finally:
        second.close(); first.close()


def test_tv_endpoints_only_from_the_laptop(client):
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    guest = {"REMOTE_ADDR": "10.0.0.5"}
    assert client.post("/api/next", json={}, environ_base=guest).status_code == 403
    e = client.post("/api/next", json={}).json["entry"]
    assert client.post("/api/done", json={"id": e["id"]}, environ_base=guest).status_code == 403
    assert client.get("/api/state").json["now_playing"]["id"] == e["id"]


def test_tv_opened_at_the_laptops_own_network_address_works(client, monkeypatch):
    import app
    monkeypatch.setattr(app, "lan_ip", lambda: "192.168.178.40")    # the address printed under the QR code on the TV
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    assert client.post("/api/next", json={}, environ_base={"REMOTE_ADDR": "192.168.178.77"}).status_code == 403  # a phone
    assert client.post("/api/next", json={}, environ_base={"REMOTE_ADDR": "192.168.178.40"}).json["entry"]["name"] == "Anna"


def test_pin_locks_out_after_five_wrong_guesses(client):
    guest = {"REMOTE_ADDR": "10.0.0.9"}
    for _ in range(5):
        assert client.post("/api/admin/check", headers={"X-Pin": "0000"}, environ_base=guest).status_code == 403
    r = client.post("/api/admin/check", headers={"X-Pin": "9999"}, environ_base=guest)
    assert r.status_code == 429  # even the right PIN waits out the lockout
    assert client.post("/api/admin/check", headers={"X-Pin": "9999"}).status_code == 200  # other devices unaffected


def test_internet_link_address_is_read_from_cloudflared():
    from app import tunnel_address
    assert tunnel_address("2026-10-28T19:50:01Z INF |  https://bold-river-tests-1234.trycloudflare.com  |") == \
        "https://bold-river-tests-1234.trycloudflare.com"
    assert tunnel_address("2026-10-28T19:50:01Z INF Starting tunnel") is None


def internet(phone):
    """How a phone's request looks after Cloudflare's tunnel: it arrives from this laptop, Cloudflare names the phone."""
    return {"environ_base": {"REMOTE_ADDR": "127.0.0.1"}, "headers": {"Cf-Connecting-Ip": phone, "Cf-Ray": "8f00-FRA"}}


def test_phones_on_the_internet_link_cant_act_as_the_tv(client):
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    assert client.post("/api/next", json={}, **internet("203.0.113.5")).status_code == 403
    assert client.get("/api/state", **internet("203.0.113.5")).status_code == 200   # guests still see everything
    assert client.post("/api/next", json={}).json["entry"]["name"] == "Anna"                 # the TV on the laptop itself


def test_wrong_pins_over_the_internet_lock_out_that_phone_only(client):
    for _ in range(5):
        r = client.post("/api/admin/check", **{**internet("203.0.113.5"), "headers": {**internet("203.0.113.5")["headers"], "X-Pin": "0000"}})
        assert r.status_code == 403
    staff = internet("198.51.100.7")
    assert client.post("/api/admin/check", environ_base=staff["environ_base"], headers={**staff["headers"], "X-Pin": "9999"}).status_code == 200


def test_the_default_pin_is_refused_over_the_internet(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"port": 5000}))           # PIN still 1234
    c = create_app(tmp_path).test_client()
    phone = internet("203.0.113.5")
    r = c.post("/api/admin/check", environ_base=phone["environ_base"], headers={**phone["headers"], "X-Pin": "1234"})
    assert r.status_code == 409 and r.json["error"] == "pin_too_easy"
    assert c.post("/api/admin/check", headers={"X-Pin": "1234"}).status_code == 200  # on the pub's own network: fine


def test_save_survives_a_briefly_locked_state_file(tmp_path, monkeypatch):
    from pathlib import Path as P
    real, calls = P.replace, []
    def flaky(self, target):
        calls.append(1)
        if len(calls) < 3:
            raise PermissionError("locked by antivirus")
        return real(self, target)
    monkeypatch.setattr(P, "replace", flaky)
    p = Party(dict(SONGS), path=tmp_path / "state.json", now=lambda: 1.0)
    p.add("Anna", "d1", "s1")
    assert (tmp_path / "state.json").exists() and len(p.queue) == 1


# ---------------------------------------------------------------- public release hardening

def test_a_faked_cloudflare_header_on_the_wifi_doesnt_dodge_the_lockout(client):
    phone = {"REMOTE_ADDR": "10.0.0.9"}  # on the venue's Wi-Fi, claiming a new internet address with every guess
    for i in range(5):
        client.post("/api/admin/check", headers={"X-Pin": "0000", "Cf-Connecting-Ip": f"203.0.113.{i}"}, environ_base=phone)
    r = client.post("/api/admin/check", headers={"X-Pin": "9999", "Cf-Connecting-Ip": "203.0.113.99"}, environ_base=phone)
    assert r.status_code == 429


def test_many_wrong_pins_over_the_internet_close_it_for_everyone(client):
    for i in range(30):  # one attacker with many addresses, one guess each
        phone = internet(f"203.0.113.{i}")
        client.post("/api/admin/check", environ_base=phone["environ_base"], headers={**phone["headers"], "X-Pin": "0000"})
    staff = internet("198.51.100.7")
    assert client.post("/api/admin/check", environ_base=staff["environ_base"], headers={**staff["headers"], "X-Pin": "9999"}).status_code == 429
    assert client.post("/api/admin/check", headers={"X-Pin": "9999"}).status_code == 200  # the laptop still gets in


def test_a_pin_with_odd_characters_is_just_wrong(client):
    assert client.post("/api/admin/check", headers={"X-Pin": "ü"}).status_code == 403


def test_guests_cant_send_commands_to_the_song_maker(client):
    assert client.post("/api/wish", json={"name": "Anna", "device": "d1", "text": "RETIME a-b"}).status_code == 400


def test_a_wish_is_remembered_once(client, tmp_path, monkeypatch):
    import app
    monkeypatch.setattr(app, "karaoke_videos", lambda text: [])
    for name in ("Anna", "Ben"):
        client.post("/api/wish", json={"name": name, "device": name, "text": "Nobody - Unknown Song"})
    assert (tmp_path / "wishes.txt").read_text(encoding="utf-8").splitlines() == ["Nobody - Unknown Song"]


def test_the_wifi_password_stays_off_the_internet(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "9999", "wifi_name": "Bar", "wifi_password": "secret"}))
    c = create_app(tmp_path).test_client()
    assert c.get("/api/state").json["wifi"] == {"name": "Bar", "password": "secret"}  # the TV and the table cards
    assert c.get("/api/state", **internet("203.0.113.5")).json["wifi"]["password"] == ""


def test_tv_endpoints_need_json_and_the_laptops_address(client):
    client.post("/api/queue", json={"name": "Anna", "device": "d1", "song_id": "a-b"})
    assert client.post("/api/next").status_code == 403  # a plain form post, which any website can send
    assert client.post("/api/next", json={}, base_url="http://evil.example:5000").status_code == 403  # DNS rebinding
    assert client.post("/api/next", json={}, base_url="http://127.0.0.1:5000").json["entry"]["name"] == "Anna"


def test_the_tv_is_only_opened_by_address():
    from app import local_host
    assert all(map(local_host, ["localhost:5000", "localhost", "127.0.0.1:5000", "192.168.1.20:5000", "[::1]:5000"]))
    assert not any(map(local_host, ["evil.example:5000", "localhost.evil.example", ""]))


def test_first_start_writes_settings_with_a_random_pin(tmp_path):
    import re
    s = create_app(tmp_path).config["settings"]
    assert re.fullmatch(r"\d{6}", s["pin"])
    assert json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))["pin"] == s["pin"]


def test_the_queue_has_a_ceiling():
    from app import MAX_QUEUE
    p = Party(dict(SONGS), songs_per_singer=1)
    for i in range(MAX_QUEUE):
        p.add(f"Singer {i}", "d", "s1")
    with pytest.raises(QueueError, match="full"):
        p.add("One more", "d", "s1")


def test_names_lose_invisible_characters():
    assert clean_name("An\u202ena\u200b") == "Anna"


def test_pages_get_security_headers(client):
    h = client.get("/").headers
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"] and "unsafe" not in h["Content-Security-Policy"]
    assert h["X-Content-Type-Options"] == "nosniff" and h["Referrer-Policy"] == "no-referrer"


def test_staff_set_the_venue_look_but_nothing_unsafe(client):
    pin = {"X-Pin": "9999"}
    ok = {"look": "neon", "accent": "#ff3366", "icon": "🎸", "pub_name": "Bar & Grill", "shelves": ["ready", "irish"]}
    assert client.post("/api/admin/settings", json=ok, headers=pin).status_code == 200
    st = client.get("/api/state").json
    assert st["look"] == {"look": "neon", "accent": "#ff3366", "icon": "🎸"} and st["shelves"] == ["ready", "irish"]
    for bad in ({"accent": "red;background:url(x)"}, {"icon": "<svg>"}, {"shelves": ["nope"]}, {"shelves": [["ready"]]},
                {"look": "matrix"}, {"pub_name": " "}, {"pin": "0000"}):
        assert client.post("/api/admin/settings", json=bad, headers=pin).status_code == 400, bad
