"""Build the standalone Windows batch installer from distributable application files only."""
import base64
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "LICENSE", "README.md", "SECURITY.md", "app.py", "catalog.py", "make_songs.py",
    "operations.py", "tv_link.py", "run_karaoke.py", "requirements.txt", "requirements-maker.txt",
    "starter-songs.txt", "setup.bat", "start-karaoke.bat", "install-autostart.ps1", "Setup-Pub-PC.bat",
    "windows/pub-pc.ps1", "windows/laptop-bootstrap.bat", "windows/laptop.ps1", "docs/pub-pc-setup.md",
)


def build(root, dest):
    dest.mkdir(exist_ok=True, parents=True)
    archive = dest / "pub-karaoke-windows.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name in FILES:
            z.write(root / name, name)
        for path in sorted((root / "static").rglob("*")):
            if path.is_file() and not path.is_symlink():
                z.write(path, path.relative_to(root))
    package = archive.read_bytes()
    template = (root / "Setup-Pub-PC.bat").read_text(encoding="ascii")
    payload = base64.b64encode(package).decode("ascii")
    (dest / "Setup-Pub-PC.bat").write_text(
        template.rstrip() + f"\n# PUBPACKAGE {hashlib.sha256(package).hexdigest()} {payload}\n",
        encoding="ascii", newline="\r\n")


if __name__ == "__main__":
    build(ROOT, ROOT / "dist")
