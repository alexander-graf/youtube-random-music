# YouTube Zufallsmusik

PyQt6-App: sucht seltene Musik auf YouTube (yt-dlp) und spielt sie ohne Browser über mpv.
Installation/Update: `./install_desktop.sh` (legt `venv/` an, aktualisiert yt-dlp, Startmenü-Eintrag
`youtube-random-music.desktop`). Start: `./run.sh`.

## Aufbau
- `main.py` Oberfläche (deutsch), `theme.py` Stylesheet
- `yt_search.py` Suche, `mpv_player.py` mpv über JSON-IPC, `mpris.py` MPRIS (dbus-fast, eigener Thread)
- `storage.py` Daten in `~/.local/share/youtube-random-music/` (playlists, verlauf, begriffe, einstellungen)
- `query_generator.py` Vorgabe-Begriffe; Anwender-Änderungen liegen in `begriffe.json` und haben Vorrang

## Fallstricke
- **Nicht `ytsearchN:` benutzen**: liefert seit 2026 keine Aufrufzahl/Kanal → alles fiel durch den
  Views-Filter. Gesucht wird über die Ergebnisseite mit `sp=EgIQAQ%253D%253D` (nur Videos).
- yt-dlp braucht für YouTube eine JS-Laufzeit; hier `node` (deno ist nicht installiert). mpv bekommt
  yt-dlp-Pfad und `js-runtimes` explizit mit, weil es auf Gentoo kein System-yt-dlp gibt.
- MPRIS-Name `org.mpris.MediaPlayer2.youtube_random_music`; Mediatasten laufen über `playerctl`,
  Test: `playerctl -p youtube_random_music status`.
- Test ohne Fenster: `QT_QPA_PLATFORM=offscreen`, mit eigenem `XDG_DATA_HOME`, damit der echte
  Verlauf nicht vollläuft.
