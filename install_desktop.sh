#!/bin/bash
# Creates a desktop shortcut for the Linux system

# Clean up old German desktop shortcut if it exists
OLD_DESKTOP_FILE="$HOME/.local/share/applications/youtube-zufall.desktop"
if [ -f "$OLD_DESKTOP_FILE" ]; then
    rm "$OLD_DESKTOP_FILE"
fi

DESKTOP_FILE="$HOME/.local/share/applications/youtube-random-music.desktop"
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Creating system desktop launcher..."

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=YouTube Random Music Dashboard
Comment=Listen to ad-free random/obscure music from YouTube via MPV
Exec=$PROJECT_DIR/run.sh
Icon=$PROJECT_DIR/app_icon.png
Terminal=false
Categories=AudioVideo;Audio;Music;Player;
StartupNotify=true
StartupWMClass=main.py
EOF

chmod +x "$DESKTOP_FILE"
echo "Installation complete! You can now find the app in your system application menu under 'YouTube Random Music Dashboard'."
