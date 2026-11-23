"""Dauerhafte Daten der App: Playlists, Verlauf, Begriffe, Einstellungen.

Alles liegt als JSON unter ~/.local/share/youtube-random-music/ (bzw.
$XDG_DATA_HOME), damit es Neuinstallationen des Programmordners übersteht.
"""
import json
import os
import shutil
import time

APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(
    os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),
    "youtube-random-music",
)

PLAYLISTS_FILE = os.path.join(DATA_DIR, "playlists.json")
HISTORY_FILE = os.path.join(DATA_DIR, "verlauf.json")
TERMS_FILE = os.path.join(DATA_DIR, "begriffe.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "einstellungen.json")

HISTORY_LIMIT = 5000  # ältere Einträge fallen raus


def _ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (OSError, json.JSONDecodeError) as e:
        print(f"Konnte {path} nicht lesen: {e}")
        # Kaputte Datei nicht überschreiben, sondern beiseitelegen
        try:
            shutil.copy(path, path + ".kaputt")
        except OSError:
            pass
        return default


def save_json(path, data):
    """Schreibt atomar (erst Temp-Datei, dann umbenennen), damit ein Absturz
    beim Speichern die Datei nicht halb leer zurücklässt."""
    _ensure_dir()
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError as e:
        print(f"Konnte {path} nicht speichern: {e}")


def load_playlists():
    if not os.path.exists(PLAYLISTS_FILE):
        # Einmalige Übernahme aus dem alten Ort im Programmordner
        old = os.path.join(APP_DIR, "playlists.json")
        if os.path.exists(old):
            _ensure_dir()
            shutil.copy(old, PLAYLISTS_FILE)
    return load_json(PLAYLISTS_FILE, {})


def save_playlists(playlists):
    save_json(PLAYLISTS_FILE, playlists)


class History:
    """Gehörte Titel, neueste zuletzt. Dient zum Ausblenden und zum Wiederfinden."""

    def __init__(self):
        entries = load_json(HISTORY_FILE, [])
        self.entries = entries if isinstance(entries, list) else []
        self.ids = {e.get("id") for e in self.entries}

    def add(self, song):
        self.entries = [e for e in self.entries if e.get("id") != song["id"]]
        entry = {k: song.get(k) for k in
                 ("id", "url", "title", "channel", "duration", "duration_string", "view_count")}
        entry["gehoert_am"] = time.strftime("%Y-%m-%d %H:%M")
        self.entries.append(entry)
        self.entries = self.entries[-HISTORY_LIMIT:]
        self.ids = {e.get("id") for e in self.entries}
        save_json(HISTORY_FILE, self.entries)

    def clear(self):
        self.entries = []
        self.ids = set()
        save_json(HISTORY_FILE, self.entries)

    def __contains__(self, song_id):
        return song_id in self.ids


def load_settings():
    return load_json(SETTINGS_FILE, {})


def save_settings(settings):
    save_json(SETTINGS_FILE, settings)
