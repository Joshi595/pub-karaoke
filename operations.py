"""Local operations shared by the server, supervisor and song maker."""
import hashlib
import json
import os
import shutil
import signal
import subprocess
import time
import uuid
import zipfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path


METADATA = ("settings.json", "state.json", "history.json", "catalog-status.json", "guests.json",
            "wishes.txt", "needs-attention.txt", "starter-songs.txt")
SONG_FILES = ("song.json", "lyrics.json", "instrumental.m4a", "vocals.m4a")


def completed_song(folder):
    """A directory's existence alone does not make it a playable song."""
    try:
        if not all((folder / n).is_file() and (folder / n).stat().st_size for n in SONG_FILES):
            return False
        song = json.loads((folder / "song.json").read_text(encoding="utf-8"))
        lyrics = json.loads((folder / "lyrics.json").read_text(encoding="utf-8"))
        return (isinstance(song, dict) and isinstance(song.get("artist"), str)
                and isinstance(song.get("title"), str) and isinstance(lyrics, list)
                and all(isinstance(l, dict) and isinstance(l.get("words"), list)
                        and isinstance(l.get("text"), str) and isinstance(l.get("start"), (int, float))
                        and isinstance(l.get("end"), (int, float)) for l in lyrics))
    except (OSError, ValueError, TypeError):
        return False


def stop_process(p):
    """End children too: venv launchers, ffmpeg and downloader helpers must not survive a timeout."""
    if p is None or p.poll() is not None:
        return
    if os.name == "nt":
        try:
            result = subprocess.run(["taskkill", "/PID", str(p.pid), "/T", "/F"], capture_output=True, timeout=15)
            if result.returncode and p.poll() is None:
                p.kill()
        except (OSError, subprocess.TimeoutExpired):
            if p.poll() is None:
                p.kill()
    else:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()


def process_options():
    return ({"creationflags": subprocess.BELOW_NORMAL_PRIORITY_CLASS} if os.name == "nt"
            else {"start_new_session": True})


@contextmanager
def maker_lock(work, name="maker.lock"):
    """OS-owned lock: scheduled and live workers cannot write the same song concurrently."""
    work.mkdir(parents=True, exist_ok=True)
    with (work / name).open("a+b") as handle:
        handle.seek(0); handle.write(b"0"); handle.flush(); handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def backup(root, include_library=False, keep=7):
    """Seven metadata snapshots plus one incremental library copy. Never delete source songs."""
    root = Path(root).resolve()
    dest = root / "backups"
    dest.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f") + "-" + uuid.uuid4().hex[:8]
    target = dest / (stamp + ".zip")
    tmp = target.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [*(root / n for n in METADATA), *root.glob("logo-*.*")]:
            if p.is_file() and not p.is_symlink():
                z.write(p, p.name)
    tmp.replace(target)
    if include_library:
        backup_library(root)
    for old in sorted(dest.glob("*.zip"))[:-keep]:
        old.unlink()
    return target


def backup_library(root):
    root = Path(root).resolve()
    library, mirror = root / "library", root / "backups" / "library"
    settings_path = root / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8-sig")) if settings_path.exists() else {}
    reserve = max(1, settings.get("min_free_gb", 5)) * 1e9
    for src in library.rglob("*"):
        if not src.is_file() or src.is_symlink() or src.name.endswith(".tmp"):
            continue
        dst = mirror / src.relative_to(library)
        if dst.exists() and dst.stat().st_size == src.stat().st_size and dst.stat().st_mtime_ns == src.stat().st_mtime_ns:
            continue
        if shutil.disk_usage(root).free < src.stat().st_size + reserve:
            raise OSError("Not enough free space for library backup")
        dst.parent.mkdir(parents=True, exist_ok=True)
        pending = dst.with_name(dst.name + ".tmp")
        shutil.copy2(src, pending)
        pending.replace(dst)


def restore(root, archive, include_library=False):
    """Restore only known venue files; reject archive traversal and unexpected members."""
    root = Path(root).resolve()
    mirror = root / "backups" / "library"
    if include_library and not mirror.is_dir():
        raise ValueError("No library backup found")
    with zipfile.ZipFile(archive) as z:
        for member in z.infolist():
            name = member.filename
            if name not in METADATA and not (Path(name).name == name and name.startswith("logo-")
                                              and Path(name).suffix.lower() in (".jpg", ".png", ".webp")):
                raise ValueError("Unexpected file in backup")
        contents = {member.filename: z.read(member) for member in z.infolist()}
    backup(root)
    for name, content in contents.items():
        dst = root / name
        pending = dst.with_name(dst.name + ".tmp")
        pending.write_bytes(content); pending.replace(dst)
    if include_library:
        for src in mirror.rglob("*"):
            if src.is_file() and not src.is_symlink():
                dst = root / "library" / src.relative_to(mirror)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)


def token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
