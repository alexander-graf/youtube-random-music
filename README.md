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

## Usage

First, ensure you have Python 3, `mpv`, and `yt-dlp` installed.

1. **Install Dependencies:**
   Ensure the virtual environment is set up and required packages (`PyQt6`, `requests`, `yt-dlp`) are installed.
   
2. **Launch the Application:**
   Run the start script in the project directory:
   ```bash
   ./run.sh
   ```

3. **Install Desktop Launcher:**
   To add the application to your system application menu, run:
   ```bash
   ./install_desktop.sh
   ```

## File Structure

- [main.py](file:///home/alex/Projekte/youtube_zufall_musik/main.py): PyQt6 user interface, event handling, and thread coordination.
- [mpv_player.py](file:///home/alex/Projekte/youtube_zufall_musik/mpv_player.py): Controls the background `mpv` process using JSON-IPC over a Unix socket.
- [yt_search.py](file:///home/alex/Projekte/youtube_zufall_musik/yt_search.py): Asynchronously fetches YouTube search results in a background thread.
- [query_generator.py](file:///home/alex/Projekte/youtube_zufall_musik/query_generator.py): Houses the dictionary of genres, descriptors, and query-building logic.
- [run.sh](file:///home/alex/Projekte/youtube_zufall_musik/run.sh): Helper script to run the app using the virtual environment.
- [install_desktop.sh](file:///home/alex/Projekte/youtube_zufall_musik/install_desktop.sh): Shell script to register the app in the Linux desktop environment.
