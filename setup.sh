#!/usr/bin/env bash
# Pub Karaoke setup for macOS and Linux: the live app and (if you say yes) the song maker. Safe to run again.
# It never uses sudo: anything missing from the system is named, with the command that installs it.
#   ./setup.sh --no-maker   skips the song maker question
set -euo pipefail
cd "$(dirname "$0")"
TORCH=(torch==2.14.1 torchaudio==2.11.0)  # exact versions known to work together
SEPARATOR=0.47.1

hint() {  # hint <brew package> <apt package or how to get it>
  if command -v brew >/dev/null; then echo "brew install $1"
  elif command -v apt-get >/dev/null; then echo "$2"
  else echo "your package manager ($1)"; fi
}

py=""
for p in python3.12 python3; do
  if command -v "$p" >/dev/null && "$p" -c 'import sys; sys.exit(sys.version_info < (3, 10))'; then py=$p; break; fi
done
if [ -z "$py" ]; then
  echo "Python 3.10 or newer is missing (3.12 is best). Install it with: $(hint python@3.12 'sudo apt install python3 python3-venv')"
  exit 1
fi
echo "Python: $(command -v "$py")"

command -v cloudflared >/dev/null || echo "Optional, for the internet link: $(hint cloudflared 'see https://pkg.cloudflare.com')"

echo "Setting up the live app..."
[ -x .venv/bin/python ] || "$py" -m venv .venv || { echo "Couldn't make a virtual environment. On Debian/Ubuntu: sudo apt install python3-venv"; exit 1; }
.venv/bin/python -m pip install --disable-pip-version-check -q --upgrade pip
.venv/bin/python -m pip install --disable-pip-version-check -r requirements.txt
.venv/bin/python -c "import app; app.ensure_settings('.')"

answer=n
if [ "${1:-}" != "--no-maker" ]; then
  echo
  echo "The song maker turns any song a guest picks into karaoke (about 5 GB, with the AI models)."
  if [ -t 0 ]; then read -r -p "Install the song maker? [Y/n] " answer; answer=${answer:-y}; else answer=y; fi
fi
if [[ $answer =~ ^[Yy] ]]; then
  for tool in ffmpeg node; do
    command -v "$tool" >/dev/null || echo "The song maker needs $tool: $(hint "$tool" "sudo apt install ${tool/node/nodejs}")"
  done
  [ -x .venv-maker/bin/python ] || "$py" -m venv .venv-maker
  pip=(.venv-maker/bin/python -m pip install --disable-pip-version-check)
  "${pip[@]}" -q --upgrade pip
  if [ "$(uname)" = Darwin ]; then  # PyPI's macOS build uses the Apple chip where it can
    "${pip[@]}" "${TORCH[@]}"
    "${pip[@]}" -r requirements-maker.txt "audio-separator[cpu]==$SEPARATOR"
  elif command -v nvidia-smi >/dev/null; then
    echo "NVIDIA graphics card found: installing the fast version."
    "${pip[@]}" "${TORCH[@]}" --index-url https://download.pytorch.org/whl/cu126
    "${pip[@]}" -r requirements-maker.txt "audio-separator[gpu]==$SEPARATOR" "onnxruntime-gpu<1.27"
  else
    echo "No NVIDIA graphics card: installing the version for the processor. Songs take longer to make."
    "${pip[@]}" "${TORCH[@]}" --index-url https://download.pytorch.org/whl/cpu
    "${pip[@]}" -r requirements-maker.txt "audio-separator[cpu]==$SEPARATOR"
  fi
fi

echo
echo "Done. Start with ./start.sh. The staff PIN is in settings.json."
