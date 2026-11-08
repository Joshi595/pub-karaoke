"""Real-browser fault tests. Install requirements-test.txt and `playwright install chromium`."""
import json
import logging
from pathlib import Path
import shutil
import threading
import time
import wave

import pytest
from werkzeug.serving import make_server

import app

playwright = pytest.importorskip("playwright.sync_api")


def wait_js(page, expression, timeout=20000):
    """Poll through CDP without enabling unsafe-eval in the application's CSP."""
    until = time.monotonic() + timeout / 1000
    while time.monotonic() < until:
        if page.evaluate(expression):
            return
        page.wait_for_timeout(100)
    raise AssertionError("Browser condition timed out: " + expression)


@pytest.fixture(scope="module")
def browser():
    with playwright.sync_playwright() as p:
        b = p.chromium.launch(headless=True, args=["--autoplay-policy=no-user-gesture-required"])
        yield b
        b.close()


@pytest.fixture
def stage(tmp_path):
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    (tmp_path / "settings.json").write_text(json.dumps({"pin": "999999", "internet_link": False,
        "auto_download": False, "upnext_seconds": 0, "display": {"theme": "venue"}}))
    (tmp_path / "static").mkdir()
    for html in Path("static").glob("*.html"): shutil.copy2(html, tmp_path / "static" / html.name)
    folder = tmp_path / "library" / "test-track"; folder.mkdir(parents=True)
    (folder / "song.json").write_text(json.dumps({"artist": "Test", "title": "Track", "duration": 1.5, "theme": "cover"}))
    (folder / "lyrics.json").write_text("[]")
    # Audio decoding is content-based: synthetic WAV stems exercise the Web Audio lifecycle without shipped music.
    for name in ("instrumental.m4a", "vocals.m4a"):
        with wave.open(str(folder / name), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(b"\0\0" * 12000)
    web = app.create_app(tmp_path); web.static_folder = str(Path("static").resolve())
    local = make_server("127.0.0.1", 0, web, threaded=True)
    public = make_server("127.0.0.1", 0, app.PublicIngress(web), threaded=True)
    web.config["settings"]["guest_port"] = public.server_port
    for server in (local, public): threading.Thread(target=server.serve_forever, daemon=True).start()
    yield web, f"http://127.0.0.1:{local.server_port}", f"http://127.0.0.1:{public.server_port}"
    for server in (local, public): server.shutdown(); server.server_close()
    web.config["shutdown"]()


@pytest.mark.parametrize("lost_after_delivery", [False, True])
def test_tv_recovers_from_lost_completion(browser, stage, lost_after_delivery):
    web, local, _ = stage
    p = browser.new_page(reduced_motion="reduce"); errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))
    c = web.test_client()
    for name in ("First", "Second"):
        c.post("/api/queue", json={"name": name, "song_id": "test-track"})
    dropped = []
    def done(route):
        if not dropped:
            dropped.append(True)
            if lost_after_delivery: route.fetch()
            route.abort()
        else: route.continue_()
    p.route("**/api/done", done)
    try:
        p.goto(local + "/tv")
        wait_js(p, "state?.now_playing?.name === 'Second' || document.querySelector('#clapWho').textContent === 'Second'")
        wait_js(p, "!state?.now_playing && state?.queue.length === 0")
        assert dropped and not errors
        assert web.config["party"].turns == {"first": 1, "second": 1}
    finally: p.close()


def test_guest_recovery_on_a_new_browser(browser, stage):
    web, _, public = stage
    first = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    second = browser.new_context(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    try:
        p = first.new_page(); p.goto(public + "/?lang=en")
        wait_js(p, "document.getElementById('recoveryCode').value.length > 30")
        token = p.locator("#recoveryCode").input_value()
        response = first.request.post(public + "/api/queue", headers={"X-Guest-Token": token}, data={"name": "Singer", "catalog_id": "test-track"})
        assert response.ok
        q = second.new_page(); errors = []; q.on("pageerror", lambda e: errors.append(str(e)))
        q.goto(public + "/?lang=de"); q.locator("details.recovery summary").click()
        q.locator("#recoverInput").fill(token); q.locator("#recoverForm button").click()
        q.locator("#tickets").wait_for(state="visible")
        assert "Track" in q.locator("#ticketList").inner_text()
        assert not q.evaluate("document.documentElement.scrollWidth > innerWidth") and not errors
        assert web.test_client().get("/api/state").json["queue"][0]["name"] == "Singer"
    finally: first.close(); second.close()


def test_unreachable_youtube_does_not_block_ready_song(browser, stage):
    web, local, _ = stage
    party = web.config["party"]
    party.add("Video", "v", "", wish="Unavailable video", yt=["unavailable"], video=True)
    party.add("Ready", "r", "test-track")
    p = browser.new_page(reduced_motion="reduce"); refs = []
    def youtube(route):
        refs.append(route.request.headers.get("referer")); route.abort()
    p.route("https://www.youtube.com/**", youtube)
    try:
        response = p.goto(local + "/tv")
        assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
        wait_js(p, "state?.now_playing?.name === 'Ready' || document.querySelector('#clapWho').textContent === 'Ready'")
        assert refs and refs[0] == local + "/"
    finally: p.close()


def test_staff_controls_and_pause_restart(browser, stage):
    web, local, public = stage
    tv, staff = browser.new_page(reduced_motion="reduce"), browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
    errors = []; tv.on("pageerror", lambda e: errors.append(str(e))); staff.on("pageerror", lambda e: errors.append(str(e)))
    try:
        staff.goto(public + "/admin"); staff.locator("#pin").fill("999999"); staff.locator("#pinForm button").click()
        staff.locator("#panel").wait_for(state="visible")
        staff.locator("#eventToggle").click()
        wait_js(staff, "state?.event?.open === false")
        staff.locator("#eventToggle").click()
        wait_js(staff, "state?.event?.open === true")
        web.test_client().post("/api/queue", json={"name": "Singer", "song_id": "test-track"})
        tv.goto(local + "/tv"); wait_js(tv, "scene === 'singing'")
        web.test_client().post("/api/admin/pause", json={"paused": True}, headers={"X-Pin": "999999"})
        wait_js(tv, "ctx.state === 'suspended'")
        entry = web.config["party"].now_playing
        web.test_client().post("/api/admin/restart", json={"id": entry["id"]}, headers={"X-Pin": "999999"})
        wait_js(tv, "ctx.state === 'running' && current.restarts === 1")
        assert not errors
        assert not staff.evaluate("document.documentElement.scrollWidth > innerWidth")
    finally: tv.close(); staff.close()


def test_skip_during_audio_loading_keeps_next_singer(browser, stage):
    web, local, _ = stage
    c = web.test_client()
    for name in ("Skipped", "Next"):
        c.post("/api/queue", json={"name": name, "song_id": "test-track"})
    p = browser.new_page(reduced_motion="reduce"); skipped = []
    def load(route):
        if not skipped:
            skipped.append(True)
            entry = web.config["party"].now_playing
            c.post("/api/admin/skip", json={"id": entry["id"]}, headers={"X-Pin": "999999"})
            route.abort()
        else: route.continue_()
    p.route("**/instrumental.m4a", load)
    try:
        p.goto(local + "/tv")
        wait_js(p, "state?.now_playing?.name === 'Next' || document.querySelector('#clapWho').textContent === 'Next'")
        assert skipped and web.config["party"].turns == {"skipped": 1, "next": 1}
    finally: p.close()


def test_reduced_motion_stops_background_animation(browser, stage):
    _, local, _ = stage
    p = browser.new_page(reduced_motion="reduce")
    try:
        p.goto(local + "/tv")
        p.locator("#bg canvas").wait_for(state="visible")
        p.wait_for_timeout(300)
        image = p.locator("#bg canvas").evaluate("c => c.toDataURL()")
        p.wait_for_timeout(500)
        assert image == p.locator("#bg canvas").evaluate("c => c.toDataURL()")
    finally: p.close()
