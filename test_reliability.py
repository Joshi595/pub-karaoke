"""Regression coverage for unattended operation and the public listener boundary."""
import json
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from werkzeug.test import Client
from werkzeug.wrappers import Response

import app
from operations import backup, completed_song, restore, token_digest


def song(folder, title="Ready"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "song.json").write_text(json.dumps({"artist": "Test", "title": title, "duration": 1}))
    (folder / "lyrics.json").write_text("[]")
    for stem in ("instrumental.m4a", "vocals.m4a"):
        (folder / stem).write_bytes(b"audio fixture")


@pytest.fixture
def venue(tmp_path):
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "999999", "wifi_name": "Pub", "wifi_password": "private-wifi",
                                                        "internet_link": False, "auto_download": False}))
    song(tmp_path / "library" / "test-ready")
    (tmp_path / "library" / "karafuncatalog.csv").write_text(
        "Id;Artist;Title;Year;Styles;Languages;Duo;Explicit\n"
        "1;Test;Ready;2000;Pop;English;0;0\n2;Test;Hidden;2000;Pop;German;0;1\n"
        "3;Test;New;2000;Pop;English;0;0\n")
    web = app.create_app(tmp_path)
    yield web, web.test_client(), Client(app.PublicIngress(web), Response)
    web.config["shutdown"]()


def guest(client):
    r = client.post("/api/guest")
    assert r.status_code == 200
    return {"X-Guest-Token": r.json["token"]}


@pytest.mark.parametrize("payload", [[1], "oops", 3, True, None])
@pytest.mark.parametrize("route", ["/api/queue", "/api/wish", "/api/admin/settings"])
def test_malformed_bodies_are_client_errors(venue, payload, route):
    _, local, _ = venue
    r = local.post(route, data=json.dumps(payload), content_type="application/json", headers={"X-Pin": "999999"})
    assert r.status_code == 400 and r.json["error"] == "bad_request"


@pytest.mark.parametrize("headers", [{}, {"Cf-Connecting-Ip": "127.0.0.1"}, {"X-Forwarded-For": "127.0.0.1", "X-Forwarded-Host": "localhost"}])
def test_public_listener_cannot_become_local(venue, headers):
    _, local, public = venue
    for route in ("/tv", "/print", "/library/test-ready/instrumental.m4a", "/library/test-ready/song.json"):
        assert public.get(route, headers=headers).status_code == 403
    for route in ("/api/next", "/api/done"):
        assert public.post(route, json={}, headers=headers).status_code == 403
    assert public.get("/api/state", headers=headers).json["wifi"]["password"] == ""
    assert local.get("/api/state").json["wifi"]["password"] == "private-wifi"
    assert local.get("/library/test-ready/instrumental.m4a").status_code == 200


def test_public_ownership_is_server_issued_and_recoverable(venue, tmp_path):
    _, _, public = venue
    assert public.post("/api/queue", json={"name": "A", "song_id": "test-ready", "device": "fake"}).status_code == 403
    owner = guest(public)
    entry = public.post("/api/queue", json={"name": "A", "song_id": "test-ready", "device": "fake"}, headers=owner).json
    assert entry["mine"]
    other = guest(public)
    assert not public.get("/api/state?device=fake", headers=other).json["queue"][0]["mine"]
    assert public.delete("/api/queue/" + entry["id"] + "?device=fake", headers=other).status_code == 403
    # A new hostname/browser recovers the same identity; the token is never in public state or persisted plaintext.
    result = public.post("/api/guest/recover", json={"code": owner["X-Guest-Token"]}, base_url="https://new-address.example")
    assert result.json["token"] == owner["X-Guest-Token"]
    saved = (tmp_path / "guests.json").read_text()
    assert owner["X-Guest-Token"] not in saved
    assert token_digest(owner["X-Guest-Token"]) in saved
    assert public.get("/api/state", headers=owner).json["queue"][0]["mine"]
    assert public.delete("/api/queue/" + entry["id"], headers=owner).status_code == 200


def test_credentials_survive_server_restart(venue, tmp_path):
    _, _, public = venue
    owner = guest(public)
    public.post("/api/queue", json={"name": "A", "song_id": "test-ready"}, headers=owner)
    restarted = app.create_app(tmp_path)
    try:
        c = Client(app.PublicIngress(restarted), Response)
        assert c.get("/api/state", headers=owner).json["queue"][0]["mine"]
    finally:
        restarted.config["shutdown"]()


def test_filter_cannot_be_bypassed_at_submission(venue, tmp_path, monkeypatch):
    _, local, _ = venue
    monkeypatch.setattr(app, "has_synced_lyrics", lambda *_: pytest.fail("hidden song reached external lookup"))
    assert local.get("/api/search?q=Hidden").json["songs"] == []
    assert local.post("/api/queue", json={"name": "A", "catalog_id": "k2"}).json["error"] == "unknown_song"
    song(tmp_path / "library" / "test-hidden", "Hidden")
    local.get("/api/search?q=Ready")
    assert local.post("/api/queue", json={"name": "A", "song_id": "test-hidden"}).json["error"] == "unknown_song"
    assert local.post("/api/wish", json={"name": "A", "text": "Test - Hidden"}).json["error"] == "unknown_song"


def test_metadata_changes_and_incomplete_publication(venue, tmp_path):
    _, local, _ = venue
    path = tmp_path / "library" / "test-ready" / "song.json"
    data = json.loads(path.read_text()); data["help_vocals"] = 0.8; path.write_text(json.dumps(data))
    local.get("/api/browse?shelf=ready")
    local.post("/api/queue", json={"name": "A", "song_id": "test-ready"})
    assert local.post("/api/next", json={}).json["entry"]["help_vocals"] == 0.8
    broken = tmp_path / "library" / "broken"; broken.mkdir(); (broken / "song.json").write_text('{"artist":"Broken","title":"Song"}')
    assert not completed_song(broken)
    assert len(local.get("/api/browse?shelf=ready").json["songs"]) == 1
    song(broken, "Recovered")
    assert len(local.get("/api/browse?shelf=ready").json["songs"]) == 2


def test_event_close_reopen_and_reset(venue):
    web, local, public = venue
    pin = {"X-Pin": "999999"}; owner = guest(public)
    add = lambda: public.post("/api/queue", json={"name": "A", "song_id": "test-ready"}, headers=owner)
    local.post("/api/admin/event", json={"action": "close"}, headers=pin)
    assert add().json["error"] == "event_closed"
    local.post("/api/admin/event", json={"action": "open"}, headers=pin)
    assert add().status_code == 200
    entry = local.post("/api/next", json={}).json["entry"]
    assert local.post("/api/admin/event", json={"action": "start"}, headers=pin).json["error"] == "song_playing"
    local.post("/api/done", json={"id": entry["id"]})
    local.post("/api/admin/event", json={"action": "start"}, headers=pin)
    assert web.config["party"].turns == {} and web.config["party"].queue == []


def test_berlin_rollover_defers_until_song_ends(venue):
    web, local, _ = venue
    party = web.config["party"]
    tz = ZoneInfo("Europe/Berlin")
    before = datetime(2026, 11, 5, 5, 59, tzinfo=tz).timestamp()
    party.now = lambda: before; party.new_event()
    local.post("/api/queue", json={"name": "A", "song_id": "test-ready"})
    entry = local.post("/api/next", json={}).json["entry"]
    party.now = lambda: before + 120
    assert local.get("/api/state").json["event"]["date"] == "2026-11-04"
    local.post("/api/done", json={"id": entry["id"]})
    assert local.get("/api/state").json["event"]["date"] == "2026-11-05"
    assert party.turns == {}


def test_storage_limit_blocks_requested_jobs(venue, monkeypatch):
    web, local, _ = venue
    web.config["party"].can_make = True
    monkeypatch.setattr(app, "library_gb", lambda _: 1000)
    assert local.post("/api/queue", json={"name": "A", "catalog_id": "k3"}).json["error"] == "storage_full"
    assert local.post("/api/wish", json={"name": "A", "text": "New - Song"}).json["error"] == "storage_full"
    assert local.post("/api/queue", json={"name": "A", "song_id": "test-ready"}).status_code == 200


def test_completion_retries_cannot_finish_a_different_singer(venue):
    _, local, _ = venue
    for name in ("A", "B"):
        local.post("/api/queue", json={"name": name, "song_id": "test-ready"})
    first = local.post("/api/next", json={}).json["entry"]
    assert local.post("/api/done", json={"id": first["id"]}).json["ok"]
    second = local.post("/api/next", json={}).json["entry"]
    assert not local.post("/api/done", json={"id": first["id"]}).json["ok"]
    assert local.get("/api/state").json["now_playing"]["id"] == second["id"]


def test_backup_restore_and_retention(tmp_path):
    (tmp_path / "settings.json").write_text('{"pin":"private"}')
    song(tmp_path / "library" / "test-ready")
    archive = backup(tmp_path, include_library=True)
    (tmp_path / "settings.json").write_text("{}")
    restore(tmp_path, archive, include_library=True)
    assert json.loads((tmp_path / "settings.json").read_text())["pin"] == "private"
    assert completed_song(tmp_path / "backups" / "library" / "test-ready")
    for _ in range(10): backup(tmp_path)
    assert len(list((tmp_path / "backups").glob("*.zip"))) == 7


def test_backup_rejects_path_traversal(tmp_path):
    import zipfile
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as z: z.writestr("../settings.json", "{}")
    with pytest.raises(ValueError): restore(tmp_path, bad)


def test_default_pin_rotation_is_backed_up(tmp_path):
    from run_karaoke import prepare
    (tmp_path / "settings.json").write_text('{"pin":"1234","pub_name":"Pub"}')
    prepare(tmp_path)
    new = json.loads((tmp_path / "settings.json").read_text())
    assert new["pin"] != "1234" and len(new["pin"]) == 6 and new["pub_name"] == "Pub"
    assert list((tmp_path / "backups").glob("*.zip"))
    prepare(tmp_path)
    assert json.loads((tmp_path / "settings.json").read_text())["pin"] == new["pin"]


def test_sixty_phones_remain_responsive_during_slow_search(venue, monkeypatch):
    _, local, public = venue
    release, started = threading.Event(), threading.Event()
    def slow(*_):
        started.set(); release.wait(5); return True
    monkeypatch.setattr(app, "has_synced_lyrics", slow)
    owner = guest(public)
    with ThreadPoolExecutor(max_workers=16) as pool:
        pending = pool.submit(lambda: public.post("/api/queue", json={"name": "New", "catalog_id": "k3"}, headers=owner))
        assert started.wait(2)
        t0 = time.monotonic()
        statuses = list(pool.map(lambda _: Client(public.application, Response).get("/api/state").status_code, range(60)))
        assert statuses == [200] * 60 and time.monotonic() - t0 < 3
        assert local.get("/api/health").json["ok"]
        assert local.post("/api/admin/check", headers={"X-Pin": "999999"}).status_code == 200
        release.set(); assert pending.result().status_code == 200


def test_submission_rate_limit(venue):
    _, _, public = venue
    owner = guest(public)
    results = [public.post("/api/queue", json={"name": str(i), "song_id": "test-ready"}, headers=owner).status_code for i in range(6)]
    assert results == [200] * 5 + [429]


def test_worker_timeout_restarts_and_allows_the_next_song(tmp_path, monkeypatch):
    import subprocess
    from test_app import FAKE_MAKER
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "999999", "auto_download": False,
        "internet_link": False, "maker_timeout_seconds": 0.5, "min_free_gb": 0}))
    (tmp_path / "make_songs.py").write_text(FAKE_MAKER)
    maker = tmp_path / app.MAKER_PY; maker.parent.mkdir(parents=True); maker.write_text("")
    launch = subprocess.Popen
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kw: launch(
        [sys.executable, *args[1:]] if str(args[0]) == str(maker) else args, **kw))
    monkeypatch.setattr(app, "karaoke_videos", lambda _: [])
    web = app.create_app(tmp_path); c = web.test_client()
    try:
        c.post("/api/wish", json={"name": "Slow", "text": "Slow - Song"})
        until = time.monotonic() + 10
        while time.monotonic() < until and c.get("/api/state").json["queue"]:
            time.sleep(0.1)
        assert not c.get("/api/state").json["queue"]
        health = c.get("/api/admin/health", headers={"X-Pin": "999999"}).json
        assert "timeout" in health["worker"]["last_error"]
        c.post("/api/wish", json={"name": "Fast", "text": "Good - Song"})
        until = time.monotonic() + 10
        while time.monotonic() < until:
            rows = c.get("/api/state").json["queue"]
            if rows and rows[0]["status"] == "ready": break
            time.sleep(0.1)
        assert rows[0]["status"] == "ready"
        assert (tmp_path / "received.txt").read_text().splitlines().count("Slow - Song") == 2
    finally: web.config["shutdown"]()


def test_incomplete_song_is_rebuilt_instead_of_skipped(tmp_path, monkeypatch):
    import make_songs
    broken = tmp_path / "library" / "test-broken"; broken.mkdir(parents=True)
    (broken / "song.json").write_text('{"artist":"Test","title":"Broken"}')
    def reached_lookup(*_): raise RuntimeError("rebuild reached lyric lookup")
    monkeypatch.setattr(make_songs, "fetch_lrclib", reached_lookup)
    with pytest.raises(RuntimeError, match="rebuild reached"):
        make_songs.make_song({"artist": "Test", "title": "Broken"}, tmp_path / "library", tmp_path / "work", None)


def test_guest_preparation_cannot_ignore_a_full_library(tmp_path, monkeypatch):
    import subprocess
    from test_app import FAKE_MAKER
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "999999", "auto_download": False, "internet_link": False, "min_free_gb": 0}))
    (tmp_path / "make_songs.py").write_text(FAKE_MAKER.replace("time.sleep(20)", "time.sleep(0.7)"))
    maker = tmp_path / app.MAKER_PY; maker.parent.mkdir(parents=True); maker.write_text("")
    launch = subprocess.Popen
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kw: launch(
        [sys.executable, *args[1:]] if str(args[0]) == str(maker) else args, **kw))
    monkeypatch.setattr(app, "karaoke_videos", lambda _: [])
    used = [0]
    monkeypatch.setattr(app, "library_gb", lambda _: used[0])
    web = app.create_app(tmp_path); c = web.test_client()
    try:
        c.post("/api/wish", json={"name": "Slow", "text": "Slow - Song"})
        received = tmp_path / "received.txt"
        until = time.monotonic() + 5
        while not received.exists() and time.monotonic() < until: time.sleep(0.02)
        assert received.exists()
        assert c.post("/api/wish", json={"name": "Good", "text": "Good - Song"}).status_code == 200
        used[0] = 1000
        time.sleep(1)
        assert "Good - Song" not in received.read_text()
        used[0] = 0
        c.post("/api/admin/settings", json={"auto_download": False}, headers={"X-Pin": "999999"})
        until = time.monotonic() + 5
        while "Good - Song" not in received.read_text() and time.monotonic() < until: time.sleep(0.05)
        assert "Good - Song" in received.read_text()
    finally: web.config["shutdown"]()


def test_real_server_keeps_public_and_private_listeners_separate(tmp_path):
    import socket
    import subprocess
    import urllib.request
    import urllib.error
    from operations import process_options, stop_process
    held = []
    for _ in range(2):
        s = socket.socket(); s.bind(("127.0.0.1", 0)); held.append(s)
    ports = [s.getsockname()[1] for s in held]
    for s in held: s.close()
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "999999", "port": ports[0], "guest_port": ports[1],
        "internet_link": False, "auto_download": False, "wifi_password": "private"}))
    code = "import sys; from pathlib import Path; from run_karaoke import serve; serve(Path(sys.argv[1]))"
    p = subprocess.Popen([sys.executable, "-c", code, str(tmp_path)], cwd=Path(__file__).parent,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **process_options())
    local, public = [f"http://127.0.0.1:{port}" for port in ports]
    def read(base, path):
        with urllib.request.urlopen(base + path, timeout=1) as r: return json.load(r)
    try:
        until = time.monotonic() + 10
        while time.monotonic() < until:
            try:
                if read(public, "/api/health")["ok"]: break
            except OSError: time.sleep(0.1)
        assert read(local, "/api/state")["wifi"]["password"] == "private"
        assert read(public, "/api/state")["wifi"]["password"] == ""
        request = urllib.request.Request(public + "/api/next", data=b"{}", headers={"Content-Type": "application/json"})
        with pytest.raises(urllib.error.HTTPError) as e: urllib.request.urlopen(request, timeout=1)
        assert e.value.code == 403
    finally: stop_process(p)
