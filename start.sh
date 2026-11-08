#!/usr/bin/env bash
# Pub Karaoke on macOS and Linux: starts the server and opens the karaoke screen full-screen.
# Stop it with Ctrl+C here; the queue is kept for the rest of the night.
cd "$(dirname "$0")" || exit 1
[ -x .venv/bin/python ] || { echo "Run ./setup.sh first."; exit 1; }
.venv/bin/python run_karaoke.py &
server=$!
trap 'kill $server 2>/dev/null' EXIT
.venv/bin/python run_karaoke.py --wait || exit 1
.venv/bin/python run_karaoke.py --kiosk &
kiosk=$!
trap 'kill "$kiosk" "$server" 2>/dev/null || true' EXIT
wait $server
