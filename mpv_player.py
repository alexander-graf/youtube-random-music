import socket
import json
import subprocess
import os
import time

class MpvPlayer:
    def __init__(self, ipc_socket_path="/tmp/yt_zufall_mpv.sock"):
        self.ipc_socket_path = ipc_socket_path
        self.process = None
        self.current_song = None
        
    def start(self, url, song_metadata=None):
        """Starts mpv playing the given URL."""
        self.stop()
        self.current_song = song_metadata
        
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
            f"--input-ipc-server={self.ipc_socket_path}",
            "--cache=yes",
            url
        ]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for socket to be created
        for _ in range(50):
            if os.path.exists(self.ipc_socket_path):
                break
            time.sleep(0.1)
            
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

    def seek(self, seconds):
        return self._send_command(["seek", seconds, "absolute"])

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
