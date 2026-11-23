import json
import subprocess
from urllib.parse import quote_plus

from PyQt6.QtCore import QThread, pyqtSignal

from mpv_player import find_ytdlp

# sp=EgIQAQ== ist YouTubes Filter „Typ: Video“ (keine Kanäle/Playlists).
# Wichtig: nur über die Ergebnisseite liefert yt-dlp Aufrufzahl und Kanal mit.
# Das frühere „ytsearchN:“ gibt beides nicht mehr zurück, dann hatte jeder
# Treffer 0 Views und fiel durch den Mindest-Views-Filter.
SEARCH_URL = "https://www.youtube.com/results?search_query={q}&sp=EgIQAQ%253D%253D"


class SearchError(Exception):
    pass


def search_youtube(query, num_results=50, executable=None):
    """Sucht auf YouTube und gibt eine Liste von Titel-Dicts zurück."""
    cmd = [
        executable or find_ytdlp(),
        SEARCH_URL.format(q=quote_plus(query)),
        "--dump-json", "--flat-playlist",
        "--playlist-end", str(num_results),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except FileNotFoundError:
        raise SearchError("yt-dlp nicht gefunden – ./install_desktop.sh ausführen.")
    except subprocess.TimeoutExpired:
        raise SearchError("YouTube hat nicht rechtzeitig geantwortet (90 s).")

    results = []
    for line in proc.stdout.splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        video_id = d.get("id")
        if not video_id or d.get("_type") not in (None, "url", "video"):
            continue
        duration = float(d.get("duration") or 0)
        results.append({
            "id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "title": d.get("title") or "Unbekannter Titel",
            "duration": duration,
            "duration_string": d.get("duration_string") or format_duration(duration),
            "view_count": int(d.get("view_count") or 0),
            "channel": d.get("channel") or d.get("uploader") or "Unbekannter Kanal",
        })

    if not results and proc.returncode != 0:
        errors = [l for l in proc.stderr.splitlines() if "ERROR" in l]
        raise SearchError((errors[-1] if errors else proc.stderr.strip()[-300:]) or
                          f"yt-dlp beendet mit Code {proc.returncode}")
    return results


def format_duration(seconds):
    seconds = int(seconds)
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class SearchWorker(QThread):
    """Sucht im Hintergrund, damit die Oberfläche nicht einfriert."""
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, query, num_results=50, parent=None):
        super().__init__(parent)
        self.query = query
        self.num_results = num_results

    def run(self):
        try:
            self.finished_signal.emit(search_youtube(self.query, self.num_results))
        except Exception as e:
            self.error_signal.emit(str(e))
