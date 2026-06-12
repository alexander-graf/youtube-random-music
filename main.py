import sys
import os
import random
import subprocess
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSlider, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QSpinBox, QCheckBox, QFrame, QSplitter,
    QMenu, QMessageBox, QDialog, QTextEdit, QTabWidget, QComboBox, QInputDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction

# Import local modules
from query_generator import generate_random_query, GENRES
from yt_search import SearchWorker
from mpv_player import MpvPlayer

# Premium QSS stylesheet (Dark Spotify-inspired Theme)
QSS_THEME = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

QFrame#control_panel, QFrame#filter_panel, QFrame#queue_frame, QFrame#results_frame {
    background-color: #1a1a1a;
    border: 1px solid #282828;
    border-radius: 8px;
}

QLabel#title_label {
    font-size: 20px;
    font-weight: bold;
    color: #ff3366; /* Neon Red-Pink */
    padding: 10px 0px;
}

QLabel#section_title {
    font-size: 14px;
    font-weight: bold;
    color: #ffffff;
    border-bottom: 2px solid #ff3366;
    padding-bottom: 4px;
    margin-bottom: 8px;
}

QLabel#song_title_label {
    font-size: 15px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#song_channel_label {
    font-size: 12px;
    color: #aaaaaa;
}

QPushButton {
    background-color: #282828;
    color: #ffffff;
    border: 1px solid #3e3e3e;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #3e3e3e;
    border-color: #ff3366;
}

QPushButton:pressed {
    background-color: #181818;
}

/* Primary buttons */
QPushButton#search_btn, QPushButton#surprise_btn {
    background-color: #ff3366;
    color: #ffffff;
    border: none;
}

QPushButton#search_btn:hover, QPushButton#surprise_btn:hover {
    background-color: #ff5588;
}

QPushButton#search_btn:pressed, QPushButton#surprise_btn:pressed {
    background-color: #cc2255;
}

/* Media buttons (High Contrast & Large) */
QPushButton#media_prev, QPushButton#media_play, QPushButton#media_pause, QPushButton#media_stop, QPushButton#media_next {
    background-color: #2b2b2b;
    border: 2px solid #ff3366;
    border-radius: 8px;
    font-size: 20px;
    color: #ffffff;
}

QPushButton#media_prev:hover, QPushButton#media_play:hover, QPushButton#media_pause:hover, QPushButton#media_stop:hover, QPushButton#media_next:hover {
    background-color: #ff3366;
    color: #ffffff;
}

QPushButton#media_prev:pressed, QPushButton#media_play:pressed, QPushButton#media_pause:pressed, QPushButton#media_stop:pressed, QPushButton#media_next:pressed {
    background-color: #b3002d;
}

QLineEdit, QSpinBox {
    background-color: #222222;
    color: #ffffff;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus, QSpinBox:focus {
    border-color: #ff3366;
}

QTableWidget, QListWidget {
    background-color: #181818;
    color: #e0e0e0;
    border: 1px solid #282828;
    gridline-color: #252525;
    border-radius: 6px;
}

QTableWidget::item, QListWidget::item {
    padding: 8px;
    border-bottom: 1px solid #222222;
}

QTableWidget::item:selected, QListWidget::item:selected {
    background-color: #ff3366;
    color: #ffffff;
}

QHeaderView::section {
    background-color: #222222;
    color: #bbbbbb;
    padding: 6px;
    border: none;
    font-weight: bold;
}

/* Slider styling */
QSlider::groove:horizontal {
    border: 1px solid #222222;
    height: 6px;
    background: #282828;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #ff3366;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #ff3366;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #ff3366;
}

QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #282828;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #ff3366;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Tab Widget & Tab Bar styling */
QTabWidget::pane {
    border: 1px solid #282828;
    background-color: #1a1a1a;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background-color: #121212;
    color: #aaaaaa;
    border: 1px solid #282828;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 14px;
    font-weight: bold;
}

QTabBar::tab:selected, QTabBar::tab:hover {
    background-color: #1a1a1a;
    color: #ffffff;
    border-bottom: 2px solid #ff3366;
}

/* QComboBox styling */
QComboBox {
    background-color: #222222;
    color: #ffffff;
    border: 1px solid #3e3e3e;
    border-radius: 4px;
    padding: 6px;
}

QComboBox:on {
    border-color: #ff3366;
}

QComboBox QAbstractItemView {
    background-color: #1e1e1e;
    color: #ffffff;
    border: 1px solid #3e3e3e;
    selection-background-color: #ff3366;
    selection-color: #ffffff;
}
"""

class GenreInfoDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"What is {title}?")
        self.resize(500, 320)
        self.setStyleSheet(parent.styleSheet() if parent else "")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)
        
        lbl_title = QLabel(f"Genre Explanation: {title}")
        lbl_title.setObjectName("section_title")
        layout.addWidget(lbl_title)
        
        self.txt = QTextEdit()
        self.txt.setReadOnly(True)
        self.txt.setText(text)
        self.txt.setStyleSheet("""
            background-color: #222222;
            border: 1px solid #3e3e3e;
            border-radius: 4px;
            padding: 10px;
            font-size: 13px;
            line-height: 1.4;
        """)
        layout.addWidget(self.txt)
        
        btn_layout = QHBoxLayout()
        self.btn_google = QPushButton("Search Google 🌐")
        self.btn_google.clicked.connect(self.search_google)
        
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_google)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self.genre_title = title

    def search_google(self):
        url = f"https://www.google.com/search?q={self.genre_title}+music+genre"
        try:
            subprocess.Popen(["/usr/bin/google-chrome-stable", url])
        except Exception:
            import webbrowser
            webbrowser.open(url)
        self.accept()

class GenreInfoWorker(QThread):
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)
    
    def __init__(self, search_term, parent=None):
        super().__init__(parent)
        self.search_term = search_term
        
    def run(self):
        try:
            genre = self.extract_genre(self.search_term)
            wiki_title = genre.replace(" ", "_")
            
            headers = {'User-Agent': 'YoutubeRandomMusic/1.0 (alex@example.com)'}
            # Try English Wikipedia first (for universal dashboard)
            url_en = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            r = requests.get(url_en, headers=headers, timeout=3)
            
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract")
                if extract:
                    self.finished_signal.emit(genre, extract)
                    return
                    
            # Fallback to German Wikipedia
            url_de = f"https://de.wikipedia.org/api/rest_v1/page/summary/{wiki_title}"
            r = requests.get(url_de, headers=headers, timeout=3)
            if r.status_code == 200:
                data = r.json()
                extract = data.get("extract")
                if extract:
                    self.finished_signal.emit(genre, f"[No English article. German:]\n\n{extract}")
                    return
                    
            # Fallback if page not found
            self.finished_signal.emit(genre, f"No Wikipedia summary found for '{genre}'.\n\nClick the Google button below to search directly in your browser.")
        except Exception as e:
            self.error_signal.emit(str(e))
            
    def extract_genre(self, search_term):
        search_term_lower = search_term.lower()
        for g in GENRES:
            if g.lower() in search_term_lower:
                return g
        
        # clean adjectives/formats
        from query_generator import ADJECTIVES, FORMATS
        words = search_term.split()
        cleaned = []
        for w in words:
            w_clean = w.lower().strip()
            if w_clean not in [a.lower() for a in ADJECTIVES] and w_clean not in [f.lower() for f in FORMATS]:
                cleaned.append(w)
        if cleaned:
            return " ".join(cleaned)
        return search_term

class NumericTableWidgetItem(QTableWidgetItem):
    def __lt__(self, other):
        self_val = self.data(Qt.ItemDataRole.UserRole)
        other_val = other.data(Qt.ItemDataRole.UserRole)
        if self_val is not None and other_val is not None:
            return self_val < other_val
        return super().__lt__(other)

class YoutubeMusicZentrale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Random Music Dashboard 🎵")
        self.resize(1100, 700)
        self.setStyleSheet(QSS_THEME)
        
        # Set Window Icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Player and Queues
        self.player = MpvPlayer()
        self.queue = []
        self.playback_history = []
        self.search_results = []
        self.filtered_results = []
        self.played_song_ids = set()
        
        # State variables
        self.is_user_seeking = False
        self.autoplay_attempts = 0
        
        # Load Playlists
        self.playlists_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlists.json")
        self.playlists = {}
        self.load_playlists()
        
        # Initialize UI Components
        self.init_ui()
        
        # Populate playlists in UI
        self.update_playlists_ui()
        
        # Timer for polling MPV status (every 500ms)
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(500)
        self.status_timer.timeout.connect(self.update_player_status)
        self.status_timer.start()
        
    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        title = QLabel("YouTube Random Music Dashboard 🎵")
        title.setObjectName("title_label")
        header_layout.addWidget(title)
        
        self.status_label = QLabel("Ready. Discover music outside the recommendations bubble.")
        self.status_label.setStyleSheet("color: #888888; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(self.status_label)
        main_layout.addLayout(header_layout)
        
        # --- SPLITTER MAIN BODY ---
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 1. Left Panel: Filter & Control
        filter_panel = QFrame()
        filter_panel.setObjectName("filter_panel")
        filter_layout = QVBoxLayout(filter_panel)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_filter = QLabel("Search & Filters")
        lbl_filter.setObjectName("section_title")
        filter_layout.addWidget(lbl_filter)
        
        filter_layout.addWidget(QLabel("Vibe / Search Query:"))
        
        search_input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("e.g., Shoegaze, Ambient Tape...")
        
        self.what_is_this_btn = QPushButton("❔ What is this?")
        self.what_is_this_btn.setToolTip("Explains the current genre using a Wikipedia scraper")
        self.what_is_this_btn.setFixedWidth(110)
        self.what_is_this_btn.clicked.connect(self.explain_genre)
        
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.what_is_this_btn)
        filter_layout.addLayout(search_input_layout)
        
        # Vibe selection buttons
        vibe_btn_layout = QHBoxLayout()
        self.vibe_btn = QPushButton("Roll Vibe 🎲")
        self.vibe_btn.setToolTip("Writes a random music style into the search input")
        self.vibe_btn.clicked.connect(self.roll_vibe)
        
        self.surprise_btn = QPushButton("Surprise Me! ✨")
        self.surprise_btn.setObjectName("surprise_btn")
        self.surprise_btn.setToolTip("Generates a random query and starts searching immediately")
        self.surprise_btn.clicked.connect(self.trigger_surprise)
        
        vibe_btn_layout.addWidget(self.vibe_btn)
        vibe_btn_layout.addWidget(self.surprise_btn)
        filter_layout.addLayout(vibe_btn_layout)
        
        # Max views
        filter_layout.addWidget(QLabel("Maximum Views (Rarity):"))
        self.max_views_spin = QSpinBox()
        self.max_views_spin.setRange(100, 10000000)
        self.max_views_spin.setSingleStep(10000)
        self.max_views_spin.setValue(300000)  # Default: max 300k views
        self.max_views_spin.setSuffix(" Views")
        filter_layout.addWidget(self.max_views_spin)
        
        # Min views
        filter_layout.addWidget(QLabel("Minimum Views (Spam Filter):"))
        self.min_views_spin = QSpinBox()
        self.min_views_spin.setRange(0, 100000)
        self.min_views_spin.setSingleStep(100)
        self.min_views_spin.setValue(100)  # Default: min 100 views
        self.min_views_spin.setSuffix(" Views")
        filter_layout.addWidget(self.min_views_spin)
        
        # Duration min
        filter_layout.addWidget(QLabel("Minimum Duration (Minutes):"))
        self.min_dur_spin = QSpinBox()
        self.min_dur_spin.setRange(1, 120)
        self.min_dur_spin.setValue(2)  # min 2 mins
        filter_layout.addWidget(self.min_dur_spin)
        
        # Duration max
        filter_layout.addWidget(QLabel("Maximum Duration (Minutes):"))
        self.max_dur_spin = QSpinBox()
        self.max_dur_spin.setRange(1, 600)
        self.max_dur_spin.setValue(12)  # max 12 mins (filters out long mixes)
        filter_layout.addWidget(self.max_dur_spin)
        
        # Results to fetch
        filter_layout.addWidget(QLabel("Search Results Limit (yt-dlp):"))
        self.results_count_spin = QSpinBox()
        self.results_count_spin.setRange(5, 200)
        self.results_count_spin.setValue(40)
        filter_layout.addWidget(self.results_count_spin)
        
        filter_layout.addSpacing(10)
        
        # Start search button
        self.search_btn = QPushButton("Start Search 🔍")
        self.search_btn.setObjectName("search_btn")
        self.search_btn.clicked.connect(self.start_youtube_search)
        filter_layout.addWidget(self.search_btn)
        
        filter_layout.addStretch()
        splitter.addWidget(filter_panel)
        
        # 2. Middle Panel: Search Results
        results_frame = QFrame()
        results_frame.setObjectName("results_frame")
        results_layout = QVBoxLayout(results_frame)
        results_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_results = QLabel("Discovered Niche Tracks")
        lbl_results.setObjectName("section_title")
        results_layout.addWidget(lbl_results)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Song Title", "Channel", "Views", "Duration"])
        self.results_table.setSortingEnabled(True)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.results_table.itemDoubleClicked.connect(self.play_selected_result)
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_results_context_menu)
        results_layout.addWidget(self.results_table)
        
        # Actions for results
        res_actions = QHBoxLayout()
        self.play_btn = QPushButton("Play (MPV) ▶️")
        self.play_btn.clicked.connect(self.play_selected_result)
        self.add_queue_btn = QPushButton("Add to Queue ➕")
        self.add_queue_btn.clicked.connect(self.add_selected_to_queue)
        
        self.add_playlist_btn = QPushButton("Save to Playlist... 💾")
        self.add_playlist_btn.clicked.connect(self.add_selected_result_to_playlist_dialog)
        
        res_actions.addWidget(self.play_btn)
        res_actions.addWidget(self.add_queue_btn)
        res_actions.addWidget(self.add_playlist_btn)
        results_layout.addLayout(res_actions)
        
        splitter.addWidget(results_frame)
        
        # 3. Right Panel: Queue & Playlists (Tabbed)
        right_tab_widget = QTabWidget()
        
        # Tab 1: Queue
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        queue_layout.setContentsMargins(10, 10, 10, 10)
        
        self.queue_list = QListWidget()
        self.queue_list.itemDoubleClicked.connect(self.play_selected_queue)
        queue_layout.addWidget(self.queue_list)
        
        queue_actions = QHBoxLayout()
        self.remove_queue_btn = QPushButton("Remove Selected ❌")
        self.remove_queue_btn.clicked.connect(self.remove_selected_queue)
        self.clear_queue_btn = QPushButton("Clear Queue 🧹")
        self.clear_queue_btn.clicked.connect(self.clear_queue)
        
        queue_actions.addWidget(self.remove_queue_btn)
        queue_actions.addWidget(self.clear_queue_btn)
        queue_layout.addLayout(queue_actions)
        
        right_tab_widget.addTab(queue_tab, "Queue")
        
        # Tab 2: Playlists
        playlists_tab = QWidget()
        playlists_layout = QVBoxLayout(playlists_tab)
        playlists_layout.setContentsMargins(10, 10, 10, 10)
        
        # Playlist selector layout
        selector_layout = QHBoxLayout()
        self.playlist_combo = QComboBox()
        self.playlist_combo.currentTextChanged.connect(self.on_playlist_selection_changed)
        
        self.new_playlist_btn = QPushButton("＋")
        self.new_playlist_btn.setToolTip("Create new playlist")
        self.new_playlist_btn.setFixedWidth(35)
        self.new_playlist_btn.clicked.connect(self.create_playlist_ui)
        
        self.delete_playlist_btn = QPushButton("🗑️")
        self.delete_playlist_btn.setToolTip("Delete selected playlist")
        self.delete_playlist_btn.setFixedWidth(35)
        self.delete_playlist_btn.clicked.connect(self.delete_selected_playlist_ui)
        
        selector_layout.addWidget(self.playlist_combo)
        selector_layout.addWidget(self.new_playlist_btn)
        selector_layout.addWidget(self.delete_playlist_btn)
        playlists_layout.addLayout(selector_layout)
        
        # Playlist songs list
        self.playlist_songs_list = QListWidget()
        self.playlist_songs_list.itemDoubleClicked.connect(self.play_selected_playlist_song)
        playlists_layout.addWidget(self.playlist_songs_list)
        
        # Playlist actions layout
        playlist_actions = QHBoxLayout()
        self.play_playlist_btn = QPushButton("Add Playlist to Queue 🎵")
        self.play_playlist_btn.clicked.connect(self.add_playlist_to_queue)
        
        self.remove_playlist_song_btn = QPushButton("Remove Song ❌")
        self.remove_playlist_song_btn.clicked.connect(self.remove_selected_playlist_song)
        
        playlist_actions.addWidget(self.play_playlist_btn)
        playlist_actions.addWidget(self.remove_playlist_song_btn)
        playlists_layout.addLayout(playlist_actions)
        
        right_tab_widget.addTab(playlists_tab, "Playlists")
        
        splitter.addWidget(right_tab_widget)
        
        # Set splitter proportions (Filters: 25%, Results: 50%, Sidebar: 25%)
        splitter.setSizes([250, 550, 250])
        
        # --- BOTTOM PANEL: MEDIA PLAYER CONTROLS ---
        player_frame = QFrame()
        player_frame.setObjectName("control_panel")
        player_layout = QHBoxLayout(player_frame)
        player_layout.setContentsMargins(15, 10, 15, 10)
        player_layout.setSpacing(15)
        
        # Track Info (Left)
        track_info_layout = QVBoxLayout()
        track_info_layout.setSpacing(2)
        self.track_title = QLabel("No track playing")
        self.track_title.setObjectName("song_title_label")
        self.track_title.setWordWrap(True)
        self.track_title.setMaximumWidth(300)
        
        self.track_channel = QLabel("-")
        self.track_channel.setObjectName("song_channel_label")
        
        track_info_layout.addWidget(self.track_title)
        track_info_layout.addWidget(self.track_channel)
        player_layout.addLayout(track_info_layout, 2)
        
        # Media Controls & Slider (Center)
        center_controls = QVBoxLayout()
        center_controls.setSpacing(4)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons_layout.setSpacing(10)
        
        self.btn_prev = QPushButton("⏮️")
        self.btn_prev.setObjectName("media_prev")
        self.btn_prev.setToolTip("Previous Song")
        self.btn_prev.setFixedSize(80, 48)
        self.btn_prev.clicked.connect(self.play_previous_song)
        
        self.btn_play = QPushButton("▶️")
        self.btn_play.setObjectName("media_play")
        self.btn_play.setToolTip("Play")
        self.btn_play.setFixedSize(80, 48)
        self.btn_play.clicked.connect(self.play_song_action)
        
        self.btn_pause = QPushButton("⏸️")
        self.btn_pause.setObjectName("media_pause")
        self.btn_pause.setToolTip("Pause")
        self.btn_pause.setFixedSize(80, 48)
        self.btn_pause.clicked.connect(self.pause_song_action)
        
        self.btn_stop = QPushButton("⏹️")
        self.btn_stop.setObjectName("media_stop")
        self.btn_stop.setToolTip("Stop")
        self.btn_stop.setFixedSize(80, 48)
        self.btn_stop.clicked.connect(self.stop_song_action)
        
        self.btn_next = QPushButton("⏭️")
        self.btn_next.setObjectName("media_next")
        self.btn_next.setToolTip("Next Song")
        self.btn_next.setFixedSize(80, 48)
        self.btn_next.clicked.connect(self.skip_song)
        
        buttons_layout.addWidget(self.btn_prev)
        buttons_layout.addWidget(self.btn_play)
        buttons_layout.addWidget(self.btn_pause)
        buttons_layout.addWidget(self.btn_stop)
        buttons_layout.addWidget(self.btn_next)
        center_controls.addLayout(buttons_layout)
        
        # Slider + Time labels
        slider_layout = QHBoxLayout()
        self.lbl_time_current = QLabel("00:00")
        self.lbl_time_current.setFixedWidth(40)
        self.lbl_time_current.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        
        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setFixedWidth(40)
        
        slider_layout.addWidget(self.lbl_time_current)
        slider_layout.addWidget(self.progress_slider)
        slider_layout.addWidget(self.lbl_time_total)
        center_controls.addLayout(slider_layout)
        
        player_layout.addLayout(center_controls, 5)
        
        # Options & Volume & Chrome (Right)
        right_controls = QVBoxLayout()
        right_controls.setSpacing(4)
        
        options_layout = QHBoxLayout()
        self.autoplay_cb = QCheckBox("Autoplay (Continuous Radio) 📻")
        self.autoplay_cb.setChecked(True)
        self.autoplay_cb.setToolTip("Automatically searches for new tracks when the current list is exhausted")
        options_layout.addWidget(self.autoplay_cb)
        
        self.chrome_btn = QPushButton("Open in Chrome 🌐")
        self.chrome_btn.clicked.connect(self.open_current_in_chrome)
        self.chrome_btn.setToolTip("Opens the current song in the Google Chrome browser")
        options_layout.addWidget(self.chrome_btn)
        
        self.save_current_playlist_btn = QPushButton("Save... 💾")
        self.save_current_playlist_btn.setToolTip("Saves the current song to a playlist")
        self.save_current_playlist_btn.clicked.connect(self.add_current_song_to_playlist_dialog)
        options_layout.addWidget(self.save_current_playlist_btn)
        
        right_controls.addLayout(options_layout)
        
        # Volume slider
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        volume_icon = QLabel("🔊")
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self.set_player_volume)
        
        volume_layout.addWidget(volume_icon)
        volume_layout.addWidget(self.volume_slider)
        right_controls.addLayout(volume_layout)
        
        player_layout.addLayout(right_controls, 3)
        
        main_layout.addWidget(player_frame)

    # --- UI INTERACTIONS ---
    
    def explain_genre(self):
        term = self.search_input.text().strip()
        if not term:
            self.status_label.setText("Please enter a search query.")
            return
            
        self.status_label.setText("Fetching genre explanation...")
        self.what_is_this_btn.setEnabled(False)
        
        self.info_worker = GenreInfoWorker(term, self)
        self.info_worker.finished_signal.connect(self.on_genre_info_finished)
        self.info_worker.error_signal.connect(self.on_genre_info_error)
        self.info_worker.start()
        
    def on_genre_info_finished(self, genre, explanation):
        self.what_is_this_btn.setEnabled(True)
        self.status_label.setText("Genre explanation loaded.")
        dialog = GenreInfoDialog(genre, explanation, self)
        dialog.exec()
        
    def on_genre_info_error(self, err_msg):
        self.what_is_this_btn.setEnabled(True)
        self.status_label.setText(f"Error fetching genre info: {err_msg}")
        QMessageBox.warning(self, "Error", f"Error fetching genre information:\n{err_msg}")

    def roll_vibe(self):
        genre = random.choice(GENRES)
        self.search_input.setText(genre)
        self.status_label.setText(f"Vibe '{genre}' rolled.")
        
    def trigger_surprise(self):
        query = generate_random_query()
        self.search_input.setText(query)
        self.status_label.setText(f"Random search: '{query}'")
        self.start_youtube_search()
        
    def start_youtube_search(self):
        query = self.search_input.text().strip()
        if not query:
            query = generate_random_query()
            self.search_input.setText(query)
            
        num_results = self.results_count_spin.value()
        self.status_label.setText(f"Searching for '{query}'...")
        self.search_btn.setEnabled(False)
        self.surprise_btn.setEnabled(False)
        
        # Launch QThread search worker
        self.search_worker = SearchWorker(query, num_results)
        self.search_worker.finished_signal.connect(self.on_search_finished)
        self.search_worker.error_signal.connect(self.on_search_error)
        self.search_worker.start()
        
    def on_search_finished(self, results):
        self.search_btn.setEnabled(True)
        self.surprise_btn.setEnabled(True)
        self.search_results = results
        self.filter_and_display_results()
        
    def on_search_error(self, err_msg):
        self.search_btn.setEnabled(True)
        self.surprise_btn.setEnabled(True)
        self.status_label.setText(f"Search error: {err_msg}")
        QMessageBox.warning(self, "Search Error", f"An error occurred during search:\n{err_msg}")
        
    def filter_and_display_results(self):
        min_views = self.min_views_spin.value()
        max_views = self.max_views_spin.value()
        min_secs = self.min_dur_spin.value() * 60
        max_secs = self.max_dur_spin.value() * 60
        
        self.filtered_results = []
        for r in self.search_results:
            views = r["view_count"]
            dur = r["duration"]
            
            # Apply view count filters
            if views < min_views or views > max_views:
                continue
            # Apply duration filters
            if dur < min_secs or dur > max_secs:
                continue
            # Skip songs already played in this session to ensure variety
            if r["id"] in self.played_song_ids:
                continue
                
            self.filtered_results.append(r)
            
        # Update Table
        self.results_table.setSortingEnabled(False)
        self.results_table.setRowCount(0)
        for i, song in enumerate(self.filtered_results):
            self.results_table.insertRow(i)
            
            # Format view count nicely with commas
            views_formatted = f"{song['view_count']:,}"
            
            item_title = NumericTableWidgetItem(song["title"])
            item_title.setData(Qt.ItemDataRole.UserRole, song["title"].lower())
            item_title.setData(Qt.ItemDataRole.UserRole + 1, song)
            
            item_channel = NumericTableWidgetItem(song["channel"])
            item_channel.setData(Qt.ItemDataRole.UserRole, song["channel"].lower())
            
            item_views = NumericTableWidgetItem(views_formatted)
            item_views.setData(Qt.ItemDataRole.UserRole, int(song["view_count"]))
            
            item_duration = NumericTableWidgetItem(song["duration_string"])
            item_duration.setData(Qt.ItemDataRole.UserRole, float(song["duration"]))
            
            # Make items read-only
            for item in (item_title, item_channel, item_views, item_duration):
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            
            self.results_table.setItem(i, 0, item_title)
            self.results_table.setItem(i, 1, item_channel)
            self.results_table.setItem(i, 2, item_views)
            self.results_table.setItem(i, 3, item_duration)
            
        self.results_table.setSortingEnabled(True)
            
        if len(self.search_results) > 0 and len(self.filtered_results) == 0:
            self.status_label.setText(
                f"Found: {len(self.search_results)} | Filtered: 0. Tip: Increase max views or search for '{self.search_input.text().strip()} vinyl'!"
            )
        else:
            self.status_label.setText(
                f"Found: {len(self.search_results)} | Filtered (niche): {len(self.filtered_results)}"
            )
        
        # If autoplay is active and player is idle, trigger playback
        if self.autoplay_cb.isChecked() and self.player.process is None:
            if self.filtered_results:
                self.play_next_autoplay()

    # --- RESULTS TABLE INTERACTIONS ---
    
    def get_selected_result_song(self):
        row = self.results_table.currentRow()
        if row >= 0:
            item = self.results_table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole + 1)
        return None
        
    def play_selected_result(self):
        song = self.get_selected_result_song()
        if song:
            self.play_song(song)
        else:
            self.status_label.setText("No song selected in the table.")
            
    def add_selected_to_queue(self):
        song = self.get_selected_result_song()
        if song:
            self.queue.append(song)
            self.queue_list.addItem(f"{song['title']} ({song['channel']})")
            self.status_label.setText(f"Added to queue: {song['title']}")
            
    def show_results_context_menu(self, position):
        row = self.results_table.currentRow()
        if row < 0 or row >= len(self.filtered_results):
            return
            
        song = self.filtered_results[row]
        menu = QMenu()
        act_play = QAction("▶️ Play (MPV)", self)
        act_queue = QAction("➕ Add to Queue", self)
        
        # Submenu for playlists
        playlist_menu = QMenu("💾 Save to Playlist", self)
        if self.playlists:
            for p_name in sorted(self.playlists.keys()):
                action = QAction(p_name, self)
                action.triggered.connect(lambda checked, name=p_name, s=song: self.add_song_to_playlist(s, name))
                playlist_menu.addAction(action)
            playlist_menu.addSeparator()
            
        act_new_pl = QAction("＋ New Playlist...", self)
        act_new_pl.triggered.connect(lambda: self.create_playlist_and_add_song(song))
        playlist_menu.addAction(act_new_pl)
        
        act_chrome = QAction("🌐 Open in Chrome", self)
        
        act_play.triggered.connect(self.play_selected_result)
        act_queue.triggered.connect(self.add_selected_to_queue)
        act_chrome.triggered.connect(lambda: self.open_song_in_chrome(song))
        
        menu.addAction(act_play)
        menu.addAction(act_queue)
        menu.addMenu(playlist_menu)
        menu.addSeparator()
        menu.addAction(act_chrome)
        menu.exec(self.results_table.viewport().mapToGlobal(position))

    # --- QUEUE INTERACTIONS ---
    
    def play_selected_queue(self):
        row = self.queue_list.currentRow()
        if row >= 0 and row < len(self.queue):
            song = self.queue.pop(row)
            self.queue_list.takeItem(row)
            self.play_song(song)
            
    def remove_selected_queue(self):
        row = self.queue_list.currentRow()
        if row >= 0 and row < len(self.queue):
            self.queue.pop(row)
            self.queue_list.takeItem(row)
            
    def clear_queue(self):
        self.queue.clear()
        self.queue_list.clear()

    # --- PLAYBACK CORE LOGIC ---
    
    def play_song(self, song, add_to_history=True):
        if add_to_history and self.player.current_song:
            if not self.playback_history or self.playback_history[-1]["id"] != self.player.current_song["id"]:
                self.playback_history.append(self.player.current_song)

        self.player.stop()
        self.track_title.setText(song["title"])
        self.track_channel.setText(f"{song['channel']} • {song['view_count']:,} Views")
        self.status_label.setText(f"Playing: {song['title']}")
        
        # Add to played songs set
        self.played_song_ids.add(song["id"])
        
        # Start player
        self.player.start(song["url"], song)
        
        # Set initial volume from volume slider
        self.player.set_volume(self.volume_slider.value())
        
        # Reset slider
        self.progress_slider.setValue(0)
        self.lbl_time_current.setText("00:00")
        self.lbl_time_total.setText(song["duration_string"])
        
        # Highlight and scroll to the row in the table
        self.highlight_song_in_table(song["id"])

    def highlight_song_in_table(self, song_id):
        self.results_table.blockSignals(True)
        for row in range(self.results_table.rowCount()):
            item = self.results_table.item(row, 0)
            if item:
                song = item.data(Qt.ItemDataRole.UserRole + 1)
                if song and song.get("id") == song_id:
                    self.results_table.selectRow(row)
                    self.results_table.scrollToItem(item)
                    break
        self.results_table.blockSignals(False)
        
    def play_previous_song(self):
        if self.playback_history:
            prev_song = self.playback_history.pop()
            self.play_song(prev_song, add_to_history=False)
        else:
            self.status_label.setText("No previous songs in history.")

    def play_song_action(self):
        if self.player.process is None:
            if self.queue:
                self.play_selected_queue()
            elif self.filtered_results:
                self.play_selected_result()
            else:
                self.trigger_surprise()
        else:
            self.player.resume()

    def pause_song_action(self):
        if self.player.process is not None:
            self.player.pause()

    def stop_song_action(self):
        self.player.stop()
        self.track_title.setText("No track playing")
        self.track_channel.setText("-")
        self.lbl_time_current.setText("00:00")
        self.lbl_time_total.setText("00:00")
        self.progress_slider.setValue(0)
        self.status_label.setText("Playback stopped.")
            
    def skip_song(self):
        self.status_label.setText("Skipping song...")
        self.player.stop()
        self.handle_track_end()
        
    def handle_track_end(self):
        self.player.stop()
        
        # 1. Play next song in queue
        if self.queue:
            next_song = self.queue.pop(0)
            self.queue_list.takeItem(0)
            self.play_song(next_song)
            
        # 2. Autoplay radio mode
        elif self.autoplay_cb.isChecked():
            self.play_next_autoplay()
        else:
            self.track_title.setText("No track playing")
            self.track_channel.setText("-")
            self.lbl_time_current.setText("00:00")
            self.lbl_time_total.setText("00:00")
            self.progress_slider.setValue(0)
            self.status_label.setText("Playback ended.")
            
    def play_next_autoplay(self):
        unplayed_results = [r for r in self.filtered_results if r["id"] not in self.played_song_ids]
        
        if unplayed_results:
            next_song = random.choice(unplayed_results)
            self.play_song(next_song)
            self.autoplay_attempts = 0
        else:
            # We consumed all results. Fetch a new random query!
            if self.autoplay_attempts < 3:
                self.autoplay_attempts += 1
                query = generate_random_query()
                self.search_input.setText(query)
                self.status_label.setText(f"All tracks played. Starting autoplay search for '{query}'...")
                
                # Fetch new search
                self.search_worker = SearchWorker(query, self.results_count_spin.value())
                self.search_worker.finished_signal.connect(self.on_autoplay_search_finished)
                self.search_worker.error_signal.connect(self.on_autoplay_search_error)
                self.search_worker.start()
            else:
                self.status_label.setText("Autoplay stopped. No tracks found.")
                self.autoplay_attempts = 0
                
    def on_autoplay_search_finished(self, results):
        self.search_results = results
        self.filter_and_display_results()
        
    def on_autoplay_search_error(self, err_msg):
        self.status_label.setText("Autoplay search error. Retrying...")
        self.play_next_autoplay()

    # --- PLAYER STATUS UPDATES (POLLING) ---
    
    def update_player_status(self):
        if self.player.process is not None:
            if self.player.process.poll() is not None:
                self.handle_track_end()
                return
                
            if not self.is_user_seeking:
                pos, dur, paused = self.player.get_position()
                
                if dur > 0:
                    self.progress_slider.setMaximum(int(dur))
                    self.progress_slider.setValue(int(pos))
                    
                    self.lbl_time_current.setText(self.format_time(pos))
                    self.lbl_time_total.setText(self.format_time(dur))

    def format_time(self, seconds):
        mins = int(seconds) // 60
        secs = int(seconds) % 60
        return f"{mins:02d}:{secs:02d}"
        
    # --- SLIDER DRAGGING AND SEEKING ---
    
    def on_slider_pressed(self):
        self.is_user_seeking = True
        
    def on_slider_released(self):
        if self.player.process is not None:
            self.player.seek(self.progress_slider.value())
        self.is_user_seeking = False
        
    def set_player_volume(self, value):
        self.player.set_volume(value)
        
    # --- CHROME AND EXTERNAL TOOLS ---
    
    def open_song_in_chrome(self, song):
        if not song or not song.get("url"):
            return
        url = song["url"]
        try:
            self.status_label.setText(f"Opening Chrome for: {song['title']}")
            subprocess.Popen(["/usr/bin/google-chrome-stable", url])
        except Exception:
            import webbrowser
            webbrowser.open(url)
            
    def open_current_in_chrome(self):
        if self.player.current_song:
            self.open_song_in_chrome(self.player.current_song)
        else:
            self.status_label.setText("No song is currently playing.")

    # --- PLAYLIST MANAGEMENT BACKEND ---
    
    def load_playlists(self):
        import json
        if os.path.exists(self.playlists_file):
            try:
                with open(self.playlists_file, "r", encoding="utf-8") as f:
                    self.playlists = json.load(f)
            except Exception as e:
                print(f"Error loading playlists: {e}")
                self.playlists = {}
        else:
            self.playlists = {}

    def save_playlists(self):
        import json
        try:
            with open(self.playlists_file, "w", encoding="utf-8") as f:
                json.dump(self.playlists, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving playlists: {e}")

    def update_playlists_ui(self):
        current_sel = self.playlist_combo.currentText()
        
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        
        if self.playlists:
            sorted_names = sorted(list(self.playlists.keys()))
            self.playlist_combo.addItems(sorted_names)
            if current_sel in self.playlists:
                self.playlist_combo.setCurrentText(current_sel)
        self.playlist_combo.blockSignals(False)
        
        self.update_playlist_songs_list()

    def update_playlist_songs_list(self):
        self.playlist_songs_list.clear()
        current_playlist = self.playlist_combo.currentText()
        if current_playlist in self.playlists:
            songs = self.playlists[current_playlist]
            for s in songs:
                self.playlist_songs_list.addItem(f"{s['title']} ({s['channel']})")

    def on_playlist_selection_changed(self):
        self.update_playlist_songs_list()

    def create_playlist_ui(self):
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist Name:")
        if ok and name.strip():
            name = name.strip()
            if name in self.playlists:
                QMessageBox.information(self, "Info", "This playlist already exists.")
                return
            self.playlists[name] = []
            self.save_playlists()
            self.update_playlists_ui()
            self.playlist_combo.setCurrentText(name)
            self.status_label.setText(f"Playlist '{name}' created.")

    def delete_selected_playlist_ui(self):
        current = self.playlist_combo.currentText()
        if not current:
            return
        reply = QMessageBox.question(
            self, "Delete Playlist",
            f"Are you sure you want to delete the playlist '{current}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if current in self.playlists:
                del self.playlists[current]
                self.save_playlists()
                self.update_playlists_ui()
                self.status_label.setText(f"Playlist '{current}' deleted.")

    def add_playlist_to_queue(self):
        current = self.playlist_combo.currentText()
        if current in self.playlists:
            songs = self.playlists[current]
            for s in songs:
                self.queue.append(s)
                self.queue_list.addItem(f"{s['title']} ({s['channel']})")
            self.status_label.setText(f"Added {len(songs)} songs to the queue.")

    def play_selected_playlist_song(self):
        row = self.playlist_songs_list.currentRow()
        current = self.playlist_combo.currentText()
        if current in self.playlists and 0 <= row < len(self.playlists[current]):
            song = self.playlists[current][row]
            self.play_song(song)

    def remove_selected_playlist_song(self):
        row = self.playlist_songs_list.currentRow()
        current = self.playlist_combo.currentText()
        if current in self.playlists and 0 <= row < len(self.playlists[current]):
            song = self.playlists[current].pop(row)
            self.save_playlists()
            self.update_playlist_songs_list()
            self.status_label.setText(f"Removed: {song['title']}")

    def add_selected_result_to_playlist_dialog(self):
        song = self.get_selected_result_song()
        if not song:
            self.status_label.setText("No song selected in the table.")
            return
        self.show_add_to_playlist_dialog(song)

    def add_current_song_to_playlist_dialog(self):
        if self.player.current_song:
            self.show_add_to_playlist_dialog(self.player.current_song)
        else:
            self.status_label.setText("No song is currently playing.")

    def show_add_to_playlist_dialog(self, song):
        menu = QMenu(self)
        if self.playlists:
            for p_name in sorted(self.playlists.keys()):
                action = QAction(p_name, self)
                action.triggered.connect(lambda checked, name=p_name, s=song: self.add_song_to_playlist(s, name))
                menu.addAction(action)
            menu.addSeparator()
            
        act_new = QAction("＋ Create new playlist...", self)
        act_new.triggered.connect(lambda: self.create_playlist_and_add_song(song))
        menu.addAction(act_new)
        menu.exec(self.cursor().pos())

    def add_song_to_playlist(self, song, playlist_name):
        if playlist_name in self.playlists:
            if any(s["id"] == song["id"] for s in self.playlists[playlist_name]):
                self.status_label.setText(f"Song is already in playlist '{playlist_name}'.")
                return
            self.playlists[playlist_name].append(song)
            self.save_playlists()
            self.update_playlist_songs_list()
            self.status_label.setText(f"Saved to '{playlist_name}': {song['title']}")

    def create_playlist_and_add_song(self, song):
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist Name:")
        if ok and name.strip():
            name = name.strip()
            if name in self.playlists:
                self.add_song_to_playlist(song, name)
                return
            self.playlists[name] = []
            self.save_playlists()
            self.update_playlists_ui()
            self.playlist_combo.setCurrentText(name)
            self.add_song_to_playlist(song, name)

    # --- CLOSE EVENT ---
    
    def closeEvent(self, event):
        self.player.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    window = YoutubeMusicZentrale()
    window.show()
    sys.exit(app.exec())
