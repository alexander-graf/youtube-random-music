import socket
import json
import subprocess
import os
import shutil
import sys


def find_ytdlp():
    """yt-dlp aus dem venv bevorzugen (aktueller als ein Systempaket), sonst PATH."""
    venv_exe = os.path.join(os.path.dirname(sys.executable), "yt-dlp")
    if os.path.exists(venv_exe):
        return venv_exe
    return shutil.which("yt-dlp") or "yt-dlp"


def find_js_runtime():
    """yt-dlp braucht für YouTube eine JS-Laufzeit; ohne sie fehlen oft Formate."""
    for name in ("deno", "node", "bun"):
        if shutil.which(name):
            return name
    return None


def default_socket_path():
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime_dir, f"yt_zufall_mpv_{os.getuid()}.sock")


class MpvPlayer:
    def __init__(self, ipc_socket_path=None):
        self.ipc_socket_path = ipc_socket_path or default_socket_path()
        self.volume = 80
        self.process = None
        self.current_song = None
        
    def start(self, url, song_metadata=None, volume=None):
        """Starts mpv playing the given URL."""
        self.stop()
        self.current_song = song_metadata
        if volume is not None:
            self.volume = int(volume)

        # Remove socket if it already exists
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass
                
        # Start mpv in background.
        # We use --no-video for audio-only and connect to the IPC server.
        cmd = [
            "mpv",
            "--no-video",
            "--no-terminal",
            f"--input-ipc-server={self.ipc_socket_path}",
            f"--volume={self.volume}",
            "--cache=yes",
            f"--script-opts=ytdl_hook-ytdl_path={find_ytdlp()}",
        ]
        js_runtime = find_js_runtime()
        if js_runtime:
            cmd.append(f"--ytdl-raw-options-append=js-runtimes={js_runtime}")
        cmd.append(url)
        # Kein Warten auf den Socket mehr: die Lautstärke geht per Kommandozeile
        # mit, und die Statusabfrage verträgt einen noch fehlenden Socket.
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
    def _send_command(self, cmd_list):
        """Sends a JSON-IPC command to mpv and returns the response dictionary."""
        if not os.path.exists(self.ipc_socket_path):
            return None
        try:
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(0.5)
            client.connect(self.ipc_socket_path)
            payload = json.dumps({"command": cmd_list}) + "\n"
            client.sendall(payload.encode("utf-8"))
            
            # Read line-by-line. mpv sends event notifications before or after
            # command responses. We look for the response containing the "error" key.
            buffer = ""
            while True:
                chunk = client.recv(4096).decode("utf-8", errors="ignore")
                if not chunk:
                    break
                buffer += chunk
                if "\n" in buffer:
                    lines = buffer.split("\n")
                    for line in lines[:-1]:
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                            if "error" in data:
                                client.close()
                                return data
                        except json.JSONDecodeError:
                            pass
                    buffer = lines[-1]
            client.close()
        except Exception:
            pass
        return None

    def pause(self):
        return self._send_command(["set_property", "pause", True])

    def resume(self):
        return self._send_command(["set_property", "pause", False])

    def toggle_pause(self):
        return self._send_command(["cycle", "pause"])

    def set_volume(self, value):
        self.volume = int(value)
        return self._send_command(["set_property", "volume", int(value)])

    def get_position(self):
        """Returns (current_position_secs, duration_secs, is_paused)"""
        is_running = self.process is not None and self.process.poll() is None
        if not is_running:
            return 0.0, 0.0, False
            
        pos = self._send_command(["get_property", "time-pos"])
        dur = self._send_command(["get_property", "duration"])
        paused = self._send_command(["get_property", "pause"])
        
        pos_val = pos.get("data") if pos and pos.get("error") == "success" else 0.0
        dur_val = dur.get("data") if dur and dur.get("error") == "success" else 0.0
        paused_val = paused.get("data") if paused and paused.get("error") == "success" else False
        
        # Sometimes mpv returns None or empty values briefly during transitions
        if pos_val is None: pos_val = 0.0
        if dur_val is None: dur_val = 0.0
        if paused_val is None: paused_val = False
        
        return float(pos_val), float(dur_val), bool(paused_val)

    def seek(self, seconds, mode="absolute"):
        return self._send_command(["seek", seconds, mode])

    def stop(self):
        self.current_song = None
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None
        
        if os.path.exists(self.ipc_socket_path):
            try:
                os.remove(self.ipc_socket_path)
            except Exception:
                pass
