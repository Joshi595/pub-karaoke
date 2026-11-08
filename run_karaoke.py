"""Supervised local server. No cloud server or paid domain is required."""
import argparse
import atexit
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request

from operations import backup, restore, stop_process, process_options, maker_lock


def prepare(root):
    from app import ensure_settings, write_json
    path = ensure_settings(root)
    settings = json.loads(path.read_text(encoding="utf-8-sig"))
    if str(settings.get("pin", "1234")) == "1234":
        backup(root)  # keep the previous configuration private and recoverable
        settings["pin"] = f"{secrets.randbelow(1_000_000):06d}"
        if not write_json(path, settings, indent=1):
            raise OSError("Could not rotate the default staff PIN")
        print("Default staff PIN replaced. Read the new PIN in settings.json on this PC.", flush=True)


def serve(root):
    from waitress import create_server
    from app import create_app, PublicIngress, bind_exclusive
    prepare(root)
    settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
    local_port, guest_port = settings.get("port", 5000), settings.get("guest_port", 5001)
    if local_port == guest_port:
        raise ValueError("port and guest_port must differ")
    sockets, servers = [], []
    application = None
    try:
        sockets.append(bind_exclusive(local_port, "127.0.0.1"))
        sockets.append(bind_exclusive(guest_port, "0.0.0.0"))  # venue Wi-Fi guest ingress only  # nosec B104
        application = create_app(root)
        for wsgi, sock in ((application, sockets[0]), (PublicIngress(application), sockets[1])):
            servers.append(create_server(wsgi, sockets=[sock], threads=16, connection_limit=500,
                                         channel_timeout=30, ident=""))
        def cleanup():
            application.config["shutdown"]()
            for server in servers:
                server.close()
        atexit.register(cleanup)
        def quit_signal(*_):
            raise KeyboardInterrupt
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, quit_signal)
        threading.Thread(target=servers[1].run, daemon=True).start()
        application.config["start_tunnel"]()
        application.config["start_maintenance"]()
        print(f"TV: http://localhost:{local_port}/tv; guest interface: port {guest_port}", flush=True)
        servers[0].run()
    except KeyboardInterrupt:
        pass
    finally:
        if application:
            application.config["shutdown"]()
        for server in servers:
            server.close()
        for sock in sockets:
            sock.close()


def ready(url, timeout=2):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:  # local health endpoint only  # nosec B310
            return r.status == 200 and json.load(r).get("ok") is True
    except (OSError, ValueError):
        return False


def supervise(root):
    with maker_lock(root / "logs", "supervisor.lock"):
        return _supervise(root)


def _supervise(root):
    """Restart a crashed/unresponsive server. The TV is a separate kiosk process following the same queue."""
    logs = root / "logs"; logs.mkdir(exist_ok=True)
    logger = logging.getLogger("karaoke-supervisor"); logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(logs / "supervisor.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s")); logger.addHandler(handler)
    prepare(root)
    settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
    port = settings.get("port", 5000)
    # Refuse a duplicate supervisor before launching anything.
    from app import bind_exclusive
    guard = bind_exclusive(port, "127.0.0.1"); guard.close()
    child = None
    def exit_signal(*_):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, exit_signal)
    try:
        while True:
            # Rotate before opening the next child log; cap each run's log via a drain thread.
            child = subprocess.Popen([sys.executable, "-u", str(root / "app.py")], cwd=root,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     encoding="utf-8", errors="replace", **process_options())
            def drain(pipe):
                for line in pipe:
                    logger.info(line.rstrip())
            threading.Thread(target=drain, args=(child.stdout,), daemon=True).start()
            started, failures = time.monotonic(), 0
            logger.info("Server started")
            while child.poll() is None:
                time.sleep(5)
                if time.monotonic() - started < 60:
                    continue
                healthy = (ready(f"http://127.0.0.1:{port}/api/health")
                           and ready(f"http://127.0.0.1:{settings.get('guest_port', 5001)}/api/health"))
                failures = 0 if healthy else failures + 1
                if failures >= 6:
                    logger.error("Health check failed for 30 seconds; restarting server")
                    stop_process(child); break
            logger.warning("Server stopped; restarting in 5 seconds")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_process(child); handler.close()


def kiosk(root):
    with maker_lock(root / "logs", "kiosk.lock"):
        return _kiosk(root)


def _kiosk(root):
    """Keep the dedicated TV browser open; never use or terminate the user's normal browser profile."""
    settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
    url = f"http://localhost:{settings.get('port', 5000)}/tv"
    candidates = [shutil.which(n) for n in ("msedge", "google-chrome", "chromium", "chromium-browser")]
    if os.name == "nt":
        for base in (os.environ.get("ProgramFiles(x86)"), os.environ.get("ProgramFiles")):
            if base:
                candidates.extend(str(Path(base) / rel) for rel in ("Microsoft/Edge/Application/msedge.exe", "Google/Chrome/Application/chrome.exe"))
    elif sys.platform == "darwin":
        candidates.append("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    browser = next((p for p in candidates if p and Path(p).is_file()), None)
    if not browser:
        raise SystemExit("Install Microsoft Edge, Google Chrome or Chromium for the TV kiosk")
    child = None
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    try:
        while True:
            if not ready(f"http://127.0.0.1:{settings.get('port', 5000)}/api/health"):
                time.sleep(2); continue
            child = subprocess.Popen([browser, "--kiosk", "--no-first-run", "--autoplay-policy=no-user-gesture-required",
                                      f"--user-data-dir={root / '.tv-profile'}", f"--window-position={os.environ.get('TV_X', '0')},0", url],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     **({"start_new_session": True} if os.name != "nt" else {}))
            child.wait()
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        stop_process(child)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--backup", action="store_true")
    parser.add_argument("--restore", type=Path)
    parser.add_argument("--library", action="store_true", help="include the incremental song backup/restore")
    parser.add_argument("--wait", action="store_true", help="wait up to 90 seconds for server readiness")
    parser.add_argument("--kiosk", action="store_true", help="keep the TV browser open after login")
    parser.add_argument("--status", action="store_true", help="exit successfully if the local server is ready")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    if args.prepare:
        prepare(root)
    elif args.backup:
        print(backup(root, include_library=args.library))
    elif args.restore:
        # Require all server listeners to be stopped before overwriting live state.
        settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
        from app import bind_exclusive
        local = bind_exclusive(settings.get("port", 5000), "127.0.0.1")
        try:
            restore(root, args.restore, include_library=args.library)
        finally:
            local.close()
    elif args.status:
        settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
        raise SystemExit(0 if ready(f"http://127.0.0.1:{settings.get('port', 5000)}/api/health") else 1)
    elif args.wait:
        settings = json.loads((root / "settings.json").read_text(encoding="utf-8-sig"))
        for _ in range(90):
            if ready(f"http://127.0.0.1:{settings.get('port', 5000)}/api/health"):
                return
            time.sleep(1)
        raise SystemExit("Server did not become ready; see logs/supervisor.log")
    elif args.kiosk:
        kiosk(root)
    elif args.serve:
        serve(root)
    else:
        supervise(root)


if __name__ == "__main__":
    main()
