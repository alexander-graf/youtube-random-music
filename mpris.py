"""MPRIS-Schnittstelle, damit playerctl, Mediatasten und Waybar die App steuern.

dbus-fast läuft mit eigener asyncio-Schleife in einem Hintergrund-Thread.
Befehle von außen kommen als Qt-Signale im GUI-Thread an; den Zustand
(Titel, Status, Position) schiebt die App über update() herein.
"""
import asyncio
import re
import threading

from PyQt6.QtCore import QObject, pyqtSignal

try:
    from dbus_fast import BusType, Variant
    from dbus_fast.aio import MessageBus
    from dbus_fast.service import PropertyAccess, ServiceInterface, dbus_property, method, signal
except ImportError:  # ohne dbus-fast läuft die App einfach ohne MPRIS
    ServiceInterface = None

BUS_NAME = "org.mpris.MediaPlayer2.youtube_random_music"
OBJECT_PATH = "/org/mpris/MediaPlayer2"
NO_TRACK = "/org/mpris/MediaPlayer2/TrackList/NoTrack"


class MprisBridge(QObject):
    play = pyqtSignal()
    pause = pyqtSignal()
    play_pause = pyqtSignal()
    stop = pyqtSignal()
    next = pyqtSignal()
    previous = pyqtSignal()
    seek_to = pyqtSignal(float)      # Sekunden, absolut
    seek_by = pyqtSignal(float)      # Sekunden, relativ
    volume = pyqtSignal(int)         # 0–100
    raise_window = pyqtSignal()
    quit = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = {"status": "Stopped", "song": None, "position": 0.0,
                      "duration": 0.0, "volume": 80}
        self.loop = None
        self.player_iface = None
        if ServiceInterface is None:
            print("MPRIS aus: Paket dbus-fast fehlt (./install_desktop.sh ausführen).")
            return
        threading.Thread(target=self._run, daemon=True, name="mpris").start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        try:
            self.loop.run_until_complete(self._serve())
        except Exception as e:
            print(f"MPRIS aus: {e}")

    async def _serve(self):
        bus = await MessageBus(bus_type=BusType.SESSION).connect()
        bus.export(OBJECT_PATH, _Root(self))
        self.player_iface = _Player(self)
        bus.export(OBJECT_PATH, self.player_iface)
        await bus.request_name(BUS_NAME)
        await bus.wait_for_disconnect()

    def update(self, **changes):
        """Neuen Zustand übernehmen und geänderte Eigenschaften melden."""
        self.state.update(changes)
        if not (self.loop and self.player_iface):
            return
        props = {}
        if "status" in changes:
            props["PlaybackStatus"] = self.state["status"]
        if "song" in changes or "duration" in changes:
            props["Metadata"] = self.player_iface.metadata()
        if "volume" in changes:
            props["Volume"] = self.state["volume"] / 100.0
        if props:
            self.loop.call_soon_threadsafe(self.player_iface.emit_properties_changed, props)

    def seeked(self, position):
        self.state["position"] = position
        if self.loop and self.player_iface:
            self.loop.call_soon_threadsafe(self.player_iface.Seeked, int(position * 1e6))


if ServiceInterface is not None:

    class _Root(ServiceInterface):
        def __init__(self, bridge):
            super().__init__("org.mpris.MediaPlayer2")
            self.bridge = bridge

        @method()
        def Raise(self):
            self.bridge.raise_window.emit()

        @method()
        def Quit(self):
            self.bridge.quit.emit()

        @dbus_property(access=PropertyAccess.READ)
        def CanQuit(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def CanRaise(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def HasTrackList(self) -> "b":
            return False

        @dbus_property(access=PropertyAccess.READ)
        def Identity(self) -> "s":
            return "YouTube Zufallsmusik"

        @dbus_property(access=PropertyAccess.READ)
        def DesktopEntry(self) -> "s":
            return "youtube-random-music"

        @dbus_property(access=PropertyAccess.READ)
        def SupportedUriSchemes(self) -> "as":
            return []

        @dbus_property(access=PropertyAccess.READ)
        def SupportedMimeTypes(self) -> "as":
            return []

    class _Player(ServiceInterface):
        def __init__(self, bridge):
            super().__init__("org.mpris.MediaPlayer2.Player")
            self.bridge = bridge

        def metadata(self):
            song = self.bridge.state["song"]
            if not song:
                return {"mpris:trackid": Variant("o", NO_TRACK)}
            track_id = re.sub(r"[^A-Za-z0-9_]", "_", song["id"])
            duration = self.bridge.state["duration"] or song.get("duration") or 0
            return {
                "mpris:trackid": Variant("o", f"/org/mpris/MediaPlayer2/track/t{track_id}"),
                "mpris:length": Variant("x", int(duration * 1e6)),
                "mpris:artUrl": Variant("s", f"https://i.ytimg.com/vi/{song['id']}/hqdefault.jpg"),
                "xesam:title": Variant("s", song.get("title", "")),
                "xesam:artist": Variant("as", [song.get("channel", "")]),
                "xesam:url": Variant("s", song.get("url", "")),
            }

        @method()
        def Next(self):
            self.bridge.next.emit()

        @method()
        def Previous(self):
            self.bridge.previous.emit()

        @method()
        def Pause(self):
            self.bridge.pause.emit()

        @method()
        def PlayPause(self):
            self.bridge.play_pause.emit()

        @method()
        def Stop(self):
            self.bridge.stop.emit()

        @method()
        def Play(self):
            self.bridge.play.emit()

        @method()
        def Seek(self, offset: "x"):
            self.bridge.seek_by.emit(offset / 1e6)

        @method()
        def SetPosition(self, track_id: "o", position: "x"):
            self.bridge.seek_to.emit(position / 1e6)

        @method()
        def OpenUri(self, uri: "s"):
            pass

        @signal()
        def Seeked(self, position) -> "x":
            return position

        @dbus_property(access=PropertyAccess.READ)
        def PlaybackStatus(self) -> "s":
            return self.bridge.state["status"]

        @dbus_property(access=PropertyAccess.READ)
        def Metadata(self) -> "a{sv}":
            return self.metadata()

        @dbus_property()
        def Volume(self) -> "d":
            return self.bridge.state["volume"] / 100.0

        @Volume.setter
        def Volume(self, value: "d"):
            self.bridge.volume.emit(max(0, min(100, int(round(value * 100)))))

        @dbus_property(access=PropertyAccess.READ)
        def Position(self) -> "x":
            return int(self.bridge.state["position"] * 1e6)

        @dbus_property(access=PropertyAccess.READ)
        def Rate(self) -> "d":
            return 1.0

        @dbus_property(access=PropertyAccess.READ)
        def MinimumRate(self) -> "d":
            return 1.0

        @dbus_property(access=PropertyAccess.READ)
        def MaximumRate(self) -> "d":
            return 1.0

        @dbus_property(access=PropertyAccess.READ)
        def CanGoNext(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def CanGoPrevious(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def CanPlay(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def CanPause(self) -> "b":
            return True

        @dbus_property(access=PropertyAccess.READ)
        def CanSeek(self) -> "b":
            return self.bridge.state["song"] is not None

        @dbus_property(access=PropertyAccess.READ)
        def CanControl(self) -> "b":
            return True
