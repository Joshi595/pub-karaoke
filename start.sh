#!/usr/bin/env bash
# Pub Karaoke on macOS and Linux: starts the server and opens the karaoke screen full-screen.
# Stop it with Ctrl+C here; the queue is kept for the rest of the night.
cd "$(dirname "$0")"
[ -x .venv/bin/python ] || { echo "Run ./setup.sh first."; exit 1; }
port=$(.venv/bin/python -c "import json; print(json.load(open('settings.json', encoding='utf-8-sig')).get('port', 5000))" 2>/dev/null || echo 5000)
.venv/bin/python app.py &
server=$!
trap 'kill $server 2>/dev/null' EXIT
sleep 3
url="http://localhost:$port/tv"
flags=(--kiosk --no-first-run --autoplay-policy=no-user-gesture-required "--user-data-dir=$PWD/.tv-profile")
if [ "$(uname)" = Darwin ] && open -Ra "Google Chrome" 2>/dev/null; then
  open -na "Google Chrome" --args "${flags[@]}" "$url"
elif browser=$(command -v google-chrome || command -v chromium || command -v chromium-browser); then
  "$browser" "${flags[@]}" "$url" >/dev/null 2>&1 &
else  # any browser: click the screen once so it may play sound, and make it full-screen by hand
  command -v xdg-open >/dev/null && xdg-open "$url" || open "$url"
fi
wait $server
