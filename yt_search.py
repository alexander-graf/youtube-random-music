import subprocess
import json
import os
from PyQt6.QtCore import QThread, pyqtSignal

def search_youtube(query, num_results=50, executable=None):
    """
    Search YouTube using yt-dlp and parse metadata.
    Returns a list of dictionaries containing video details.
    """
    if executable is None:
        import sys
        # Dynamic path to yt-dlp inside the active virtualenv
        executable = os.path.join(sys.prefix, "bin", "yt-dlp")
        
    # Check if virtualenv yt-dlp exists, fallback to global system path if not
    if not os.path.exists(executable):
        executable = "yt-dlp"
        
    cmd = [
        executable,
        f"ytsearch{num_results}:{query}",
        "--dump-json",
        "--flat-playlist"
    ]
    
    results = []
    try:
        # Use stderr=subprocess.DEVNULL to prevent process blocking on OS pipe buffer limits
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        
        # Read output line by line as it arrives
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                video_data = json.loads(line)
                video_id = video_data.get("id")
                url = video_data.get("url") or f"https://www.youtube.com/watch?v={video_id}"
                
                # Basic view count handling (can be None)
                views = video_data.get("view_count")
                views = int(views) if views is not None else 0
                
                # Basic duration handling (can be None)
                duration = video_data.get("duration")
                duration = float(duration) if duration is not None else 0.0
                
                results.append({
                    "id": video_id,
                    "url": url,
                    "title": video_data.get("title", "Unknown Title"),
                    "duration": duration,
                    "duration_string": video_data.get("duration_string", "00:00"),
                    "view_count": views,
                    "channel": video_data.get("channel") or video_data.get("uploader") or "Unknown Channel",
                })
            except (json.JSONDecodeError, ValueError):
                pass
                
        process.wait()
    except Exception as e:
        print(f"Error during YouTube search: {e}")
        
    return results

class SearchWorker(QThread):
    """Worker thread to run the search in the background without freezing the GUI."""
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)
    
    def __init__(self, query, num_results=50, parent=None):
        super().__init__(parent)
        self.query = query
        self.num_results = num_results
        
    def run(self):
        try:
            results = search_youtube(self.query, self.num_results)
            self.finished_signal.emit(results)
        except Exception as e:
            self.error_signal.emit(str(e))
