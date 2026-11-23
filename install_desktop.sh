#!/bin/bash
# Legt das venv an (falls nötig), aktualisiert yt-dlp und trägt die App ins Startmenü ein.
# Gefahrlos mehrfach ausführbar; ein erneuter Lauf ist auch das Update für yt-dlp.
set -e
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

for tool in python3 mpv; do
    command -v "$tool" >/dev/null || { echo "Fehlt: $tool (Gentoo: emerge media-video/mpv bzw. dev-lang/python)" >&2; exit 1; }
done
command -v deno >/dev/null || command -v node >/dev/null || \
    echo "Hinweis: weder deno noch node gefunden – yt-dlp findet dann bei YouTube oft keine Formate."

if [ ! -x venv/bin/python ] || ! venv/bin/python -c "import sys" 2>/dev/null; then
    echo "Lege venv an..."
    rm -rf venv
    python3 -m venv venv
fi
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q --upgrade -r requirements.txt
echo "yt-dlp $(venv/bin/yt-dlp --version)"

# Alte Einträge aus früheren Versionen entfernen
rm -f "$HOME/.local/share/applications/youtube-zufall.desktop"

DESKTOP_FILE="$HOME/.local/share/applications/youtube-random-music.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"
cat <<DESK > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=YouTube Random Music Dashboard
GenericName=Zufallsmusik
Comment=Listen to ad-free random/obscure music from YouTube via MPV
Exec=$PROJECT_DIR/run.sh
Icon=$PROJECT_DIR/app_icon.png
Terminal=false
Categories=AudioVideo;Audio;Music;Player;
StartupNotify=true
StartupWMClass=youtube-random-music
DESK

command -v update-desktop-database >/dev/null && update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "Fertig. Im Startmenü (fuzzel): 'YouTube Random Music Dashboard'."
