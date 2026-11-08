#!/usr/bin/env bash
# Linux desktop: install a user service and an interactive TV autostart entry.
set -euo pipefail
task_root=$(cd "$(dirname "$0")" && pwd)
test -x "$task_root/.venv/bin/python" || { echo 'Run ./setup.sh first.'; exit 1; }
command -v systemctl >/dev/null || { echo 'This installer needs systemd (Linux).'; exit 1; }
mkdir -p "$HOME/.config/systemd/user" "$HOME/.config/autostart"
# Escape systemd specifiers and shell-special characters in a checked absolute path.
unit_root=${task_root//%/%%}
unit_root=${unit_root//\\/\\\\}
unit_root=${unit_root//\"/\\\"}
cat > "$HOME/.config/systemd/user/pub-karaoke.service" <<EOF
[Unit]
Description=Pub Karaoke supervised server
After=network-online.target
[Service]
WorkingDirectory="$unit_root"
ExecStart="$unit_root/.venv/bin/python" "$unit_root/run_karaoke.py"
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
EOF
cat > "$HOME/.config/autostart/pub-karaoke.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Pub Karaoke TV
Exec="$unit_root/.venv/bin/python" "$unit_root/run_karaoke.py" --kiosk
Terminal=false
EOF
systemctl --user daemon-reload
systemctl --user enable pub-karaoke.service
echo 'Installed. For boot before login, run: sudo loginctl enable-linger your-kiosk-username'
echo 'Sign in to the desktop for the TV. Reboot to test both startup paths.'
