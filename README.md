# YouTube Random Music Dashboard 🎵

An elegant PyQt6 desktop application designed to discover and play YouTube music outside the standard recommendation bubble. Built for Linux, optimized to run efficiently in the background.

## Features

1. **Browserless Playback (MPV Integration):**
   - Streams audio directly via `mpv` in a background process.
   - Extremely resource-efficient (no RAM overhead from browser tabs).
   - **Ad-Free:** Media streaming via `yt-dlp` and `mpv` typically bypasses standard web ads.
   - Full playback controls (Play/Pause, volume, progress slider, and skip track) embedded in the GUI.

2. **Niche & Rare Music Discovery:**
   - **View Count Filter:** Set a maximum view threshold (e.g., max. 50,000 views) to find true hidden gems and niche uploads.
   - **Spam Protection:** Set a minimum view threshold (e.g., min. 100 views) to filter out empty or broken uploads.
   - **Duration Filter:** Exclude long mixes (e.g., 10-hour loops) or very short audio snippets.

3. **Random Queries & Surprise Search:**
   - **Roll a Vibe 🎲:** Pick a random niche genre from an extensive internal list (e.g., *Darkjazz*, *Dungeon Synth*, *Krautrock*, *Math Rock*, *Vaporwave*) and load it into the search box.
   - **Surprise Me! ✨:** Generates a random query mixing descriptors (e.g., *obscure*, *rare*, *forgotten*), genres, and formats (e.g., *cassette*, *demo*, *vinyl*) to instantly kick off a search for rare tape rips or demo records.

4. **Continuous Radio (Autoplay):**
   - Automatically jumps to the next song when the current one finishes.
   - Once the list is completed, the app automatically generates a new random query search and keeps playing—providing an endless, ad-free stream of obscure tunes.

5. **Web Browser Integration:**
   - Open the currently playing track in your default web browser (like Google Chrome) with a single click to like, comment, or save it to a playlist.

## Since v1.1

- German UI; filters apply instantly; the results panel shows why tracks were hidden.
- "Not music" filter: titles with words like *review*, *documentary*, *tutorial* are hidden
  (editable under "Begriffe & Ausschlüsse").
- Listening history persists across restarts (tab "Verlauf"); already heard tracks can be hidden.
- Own genres/words for the random search, stored in `~/.local/share/youtube-random-music/`.
- MPRIS: media keys, `playerctl` and Waybar control the player.

## Usage

System requirements: Python 3, `mpv`, and a JavaScript runtime for yt-dlp (`deno` or `node`).
PyQt6, requests and yt-dlp live in a local `venv/`.

1. **Install (also the yt-dlp update):**
   ```bash
   ./install_desktop.sh
   ```
   Creates `venv/` if missing, installs/upgrades `requirements.txt`, and adds
   "YouTube Random Music Dashboard" to the application menu. Re-run it when
   YouTube playback breaks — usually yt-dlp just needs an update.

2. **Launch:** from the application menu, or `./run.sh`.

## File Structure

- [main.py](file:///home/alex/Projekte/youtube_zufall_musik/main.py): PyQt6 user interface, event handling, and thread coordination.
- [mpv_player.py](file:///home/alex/Projekte/youtube_zufall_musik/mpv_player.py): Controls the background `mpv` process using JSON-IPC over a Unix socket.
- [yt_search.py](file:///home/alex/Projekte/youtube_zufall_musik/yt_search.py): Asynchronously fetches YouTube search results in a background thread.
- [query_generator.py](file:///home/alex/Projekte/youtube_zufall_musik/query_generator.py): Houses the dictionary of genres, descriptors, and query-building logic.
- [run.sh](file:///home/alex/Projekte/youtube_zufall_musik/run.sh): Helper script to run the app using the virtual environment.
- [install_desktop.sh](file:///home/alex/Projekte/youtube_zufall_musik/install_desktop.sh): Shell script to register the app in the Linux desktop environment.
