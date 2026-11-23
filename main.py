import os
import random
import shutil
import subprocess
import sys
import webbrowser
from urllib.parse import quote, quote_plus

import requests
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFrame, QHBoxLayout, QHeaderView,
    QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QSlider, QSpinBox, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

import query_generator as qg
import storage
from mpris import MprisBridge
from mpv_player import MpvPlayer
from theme import QSS_THEME
from yt_search import SearchWorker

SONG_ROLE = Qt.ItemDataRole.UserRole + 1
SONG_KEYS = ("id", "url", "title", "channel", "duration", "duration_string", "view_count")


def open_url(url):
    """Chrome bevorzugen, wenn installiert, sonst den Standardbrowser."""
    chrome = shutil.which("google-chrome-stable") or shutil.which("google-chrome")
    if chrome:
        try:
            subprocess.Popen([chrome, url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
            return
        except OSError:
            pass
    webbrowser.open(url)


def song_label(song):
    return f"{song.get('title', '?')} ({song.get('channel', '?')})"


def song_item(song, text=None):
    item = QListWidgetItem(text or song_label(song))
    item.setData(SONG_ROLE, song)
    return item


def fmt_views(n):
    return f"{n:,}".replace(",", ".")


# --- Genre-Erklärung -------------------------------------------------------

class GenreInfoDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Was ist {title}?")
        self.resize(520, 340)
        self.genre_title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        lbl = QLabel(title)
        lbl.setObjectName("section_title")
        layout.addWidget(lbl)

        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setText(text)
        layout.addWidget(txt)

        buttons = QHBoxLayout()
        btn_google = QPushButton("Bei Google suchen 🌐")
        btn_google.clicked.connect(self.search_google)
        btn_close = QPushButton("Schließen")
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_google)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

    def search_google(self):
        open_url(f"https://www.google.com/search?q={quote_plus(self.genre_title + ' Musikrichtung')}")
        self.accept()


class GenreInfoWorker(QThread):
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, search_term, terms, parent=None):
        super().__init__(parent)
        self.search_term = search_term
        self.terms = terms

    def run(self):
        try:
            genre = self.extract_genre(self.search_term)
            wiki_title = quote(genre.replace(" ", "_"), safe="")
            headers = {"User-Agent": "YoutubeRandomMusic/1.1 (Desktop-App)"}
            for lang, prefix in (("de", ""), ("en", "[Kein deutscher Artikel, englisch:]\n\n")):
                r = requests.get(f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{wiki_title}",
                                 headers=headers, timeout=5)
                if r.status_code == 200 and r.json().get("extract"):
                    self.finished_signal.emit(genre, prefix + r.json()["extract"])
                    return
            self.finished_signal.emit(
                genre, f"Kein Wikipedia-Artikel zu „{genre}“ gefunden.\n\n"
                       "Mit dem Google-Knopf unten im Browser suchen.")
        except Exception as e:
            self.error_signal.emit(str(e))

    def extract_genre(self, term):
        lower = term.lower()
        for g in sorted(self.terms["genres"], key=len, reverse=True):
            if g.lower() in lower:
                return g
        noise = {w.lower() for w in self.terms["adjektive"] + self.terms["formate"]}
        cleaned = [w for w in term.split() if w.lower() not in noise]
        return " ".join(cleaned) or term


# --- Begriffe bearbeiten ---------------------------------------------------

class TermsDialog(QDialog):
    LABELS = {
        "genres": ("Genres", "Ein Genre pro Zeile. Jede Zufallssuche enthält genau eins."),
        "adjektive": ("Beschreibungen", "Wörter davor, z. B. „rare“, „forgotten“. "
                                        "Kommen in etwa 60 % der Zufallssuchen vor."),
        "formate": ("Formate", "Wörter dahinter, z. B. „cassette“, „1980s“. "
                               "Kommen in etwa 50 % der Zufallssuchen vor."),
        "ausschluss": ("Ausschlusswörter", "Treffer, deren Titel eines dieser Wörter enthält, "
                                           "werden ausgeblendet (ganze Wörter, Groß/klein egal). "
                                           "Gegen Reviews, Dokus, Tutorials usw."),
    }

    def __init__(self, terms, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Begriffe für die Zufallssuche")
        self.resize(560, 520)
        self.edits = {}

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        for key, (title, hint) in self.LABELS.items():
            page = QWidget()
            page_layout = QVBoxLayout(page)
            lbl = QLabel(hint)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("color: #aaaaaa;")
            edit = QPlainTextEdit("\n".join(terms[key]))
            page_layout.addWidget(lbl)
            page_layout.addWidget(edit)
            self.edits[key] = edit
            tabs.addTab(page, title)
        layout.addWidget(tabs)

        buttons = QHBoxLayout()
        btn_defaults = QPushButton("Vorgaben wiederherstellen")
        btn_defaults.clicked.connect(self.restore_defaults)
        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Speichern")
        btn_save.setObjectName("search_btn")
        btn_save.clicked.connect(self.accept)
        buttons.addWidget(btn_defaults)
        buttons.addStretch()
        buttons.addWidget(btn_cancel)
        buttons.addWidget(btn_save)
        layout.addLayout(buttons)

    def restore_defaults(self):
        for key, edit in self.edits.items():
            edit.setPlainText("\n".join(qg.DEFAULT_TERMS[key]))

    def terms(self):
        return {key: [l.strip() for l in edit.toPlainText().splitlines() if l.strip()]
                for key, edit in self.edits.items()}


class SortItem(QTableWidgetItem):
    """Tabellenzelle, die nach UserRole sortiert (Zahlen statt Text)."""

    def __lt__(self, other):
        a, b = self.data(Qt.ItemDataRole.UserRole), other.data(Qt.ItemDataRole.UserRole)
        if a is not None and b is not None:
            return a < b
        return super().__lt__(other)


# --- Hauptfenster ----------------------------------------------------------

class YoutubeMusicZentrale(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Zufallsmusik 🎵")
        self.resize(1200, 760)
        self.setStyleSheet(QSS_THEME)
        icon_path = os.path.join(storage.APP_DIR, "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.settings = storage.load_settings()
        self.terms = qg.load_terms()
        self.exclude_re = qg.build_exclude_matcher(self.terms["ausschluss"])
        self.history = storage.History()
        self.playlists = storage.load_playlists()

        self.player = MpvPlayer()
        self.mpris = MprisBridge(self)
        self.queue = []
        self.playback_history = []     # für ⏮️ in dieser Sitzung
        self.search_results = []
        self.filtered_results = []
        self.session_played = set()    # nie zweimal pro Sitzung, auch ohne Ausblenden
        self.is_user_seeking = False
        self.autoplay_attempts = 0
        self.last_paused = None
        # Such-Threads festhalten, sonst räumt Python sie mitten im Lauf weg und
        # Qt bricht ab. Nur das Ergebnis der neuesten Suche zählt.
        self.active_workers = set()
        self.search_generation = 0

        self.init_ui()
        self.apply_settings()
        self.update_playlists_ui()
        self.update_history_ui()

        m = self.mpris
        m.update(volume=self.volume_slider.value())
        m.play.connect(self.play_song_action)
        m.pause.connect(self.pause_song_action)
        m.play_pause.connect(self.toggle_pause_action)
        m.stop.connect(self.stop_song_action)
        m.next.connect(self.skip_song)
        m.previous.connect(self.play_previous_song)
        m.seek_to.connect(lambda s: self.player.seek(s))
        m.seek_by.connect(lambda s: self.player.seek(s, "relative"))
        m.volume.connect(self.volume_slider.setValue)
        m.raise_window.connect(self.bring_to_front)
        m.quit.connect(self.close)

        self.status_timer = QTimer(self)
        self.status_timer.setInterval(500)
        self.status_timer.timeout.connect(self.update_player_status)
        self.status_timer.start()

    # --- Aufbau ---

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(15, 10, 15, 15)
        main_layout.setSpacing(12)

        header = QHBoxLayout()
        title = QLabel("YouTube Zufallsmusik 🎵")
        title.setObjectName("title_label")
        header.addWidget(title)
        self.status_label = QLabel("Bereit. Musik abseits der Empfehlungsblase entdecken.")
        self.status_label.setStyleSheet("color: #888888; font-style: italic;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(self.status_label)
        main_layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        splitter.addWidget(self.build_filter_panel())
        splitter.addWidget(self.build_results_panel())
        splitter.addWidget(self.build_side_tabs())
        splitter.setSizes([260, 620, 300])

        main_layout.addWidget(self.build_player_panel())

    @staticmethod
    def spin(lo, hi, step=1, suffix=""):
        s = QSpinBox()
        s.setRange(lo, hi)
        s.setSingleStep(step)
        s.setSuffix(suffix)
        s.setGroupSeparatorShown(True)
        return s

    def button(self, text, slot, tip=None, name=None):
        b = QPushButton(text)
        b.clicked.connect(slot)
        if tip:
            b.setToolTip(tip)
        if name:
            b.setObjectName(name)
        return b

    def build_filter_panel(self):
        panel = QFrame()
        panel.setObjectName("filter_panel")
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 10, 10, 10)

        lbl = QLabel("Suche & Filter")
        lbl.setObjectName("section_title")
        lay.addWidget(lbl)

        lay.addWidget(QLabel("Suchbegriff:"))
        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("z. B. Shoegaze, Krautrock tape …")
        self.search_input.returnPressed.connect(self.start_youtube_search)
        self.what_is_this_btn = self.button("❔", self.explain_genre,
                                            "Erklärt das Genre im Suchfeld (Wikipedia)")
        self.what_is_this_btn.setFixedWidth(40)
        row.addWidget(self.search_input)
        row.addWidget(self.what_is_this_btn)
        lay.addLayout(row)

        row = QHBoxLayout()
        row.addWidget(self.button("Genre würfeln 🎲", self.roll_vibe,
                                  "Schreibt ein zufälliges Genre ins Suchfeld"))
        row.addWidget(self.button("Überrasch mich ✨", self.trigger_surprise,
                                  "Zufällige Suche bauen und sofort suchen", "surprise_btn"))
        lay.addLayout(row)

        lay.addWidget(QLabel("Höchstens Aufrufe (Seltenheit):"))
        self.max_views_spin = self.spin(100, 100_000_000, 10_000, " Aufrufe")
        lay.addWidget(self.max_views_spin)

        lay.addWidget(QLabel("Mindestens Aufrufe (gegen Leeres):"))
        self.min_views_spin = self.spin(0, 1_000_000, 100, " Aufrufe")
        lay.addWidget(self.min_views_spin)

        lay.addWidget(QLabel("Länge von … bis:"))
        row = QHBoxLayout()
        self.min_dur_spin = self.spin(0, 120, 1, " min")
        self.max_dur_spin = self.spin(1, 600, 1, " min")
        row.addWidget(self.min_dur_spin)
        row.addWidget(QLabel("–"))
        row.addWidget(self.max_dur_spin)
        lay.addLayout(row)

        lay.addWidget(QLabel("Treffer abrufen:"))
        self.results_count_spin = self.spin(10, 200, 10)
        lay.addWidget(self.results_count_spin)

        self.hide_heard_cb = QCheckBox("Schon Gehörtes ausblenden")
        self.hide_heard_cb.setToolTip("Blendet alles aus, was im Verlauf steht – auch aus früheren Sitzungen")
        lay.addWidget(self.hide_heard_cb)

        self.exclude_cb = QCheckBox("Nicht-Musik ausblenden")
        self.exclude_cb.setToolTip("Reviews, Dokus, Tutorials … (Wortliste unter „Begriffe …“)")
        lay.addWidget(self.exclude_cb)

        lay.addWidget(self.button("Begriffe & Ausschlüsse … ✏️", self.edit_terms,
                                  "Genres, Zufallswörter und Ausschlusswörter selbst pflegen"))

        lay.addSpacing(10)
        self.search_btn = self.button("Suchen 🔍", self.start_youtube_search, name="search_btn")
        lay.addWidget(self.search_btn)
        lay.addStretch()
        return panel

    def connect_filter_widgets(self):
        """Filter wirken sofort auf die vorhandenen Treffer, ohne neue Suche.
        Erst nach apply_settings verbinden, sonst filtert jeder Startwert neu."""
        for s in (self.max_views_spin, self.min_views_spin, self.min_dur_spin, self.max_dur_spin):
            s.valueChanged.connect(lambda _v: self.filter_and_display_results())
        for cb in (self.hide_heard_cb, self.exclude_cb):
            cb.toggled.connect(lambda _v: self.filter_and_display_results())

    def build_results_panel(self):
        frame = QFrame()
        frame.setObjectName("results_frame")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 10, 10, 10)

        lbl = QLabel("Gefundene Titel")
        lbl.setObjectName("section_title")
        lay.addWidget(lbl)

        t = self.results_table = QTableWidget()
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["Titel", "Kanal", "Aufrufe", "Länge"])
        t.setSortingEnabled(True)
        h = t.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h.resizeSection(1, 170)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        t.verticalHeader().setVisible(False)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.itemDoubleClicked.connect(self.play_selected_result)
        t.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        t.customContextMenuRequested.connect(self.show_results_context_menu)
        lay.addWidget(t)

        self.filter_info = QLabel("")
        self.filter_info.setStyleSheet("color: #888888;")
        self.filter_info.setWordWrap(True)
        lay.addWidget(self.filter_info)

        row = QHBoxLayout()
        row.addWidget(self.button("Abspielen ▶️", self.play_selected_result))
        row.addWidget(self.button("In Warteschlange ➕", self.add_selected_to_queue))
        row.addWidget(self.button("In Playlist … 💾", self.add_selected_result_to_playlist_dialog))
        lay.addLayout(row)
        return frame

    def build_side_tabs(self):
        tabs = QTabWidget()

        # Warteschlange
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        self.queue_list = QListWidget()
        self.queue_list.itemDoubleClicked.connect(self.play_selected_queue)
        lay.addWidget(self.queue_list)
        row = QHBoxLayout()
        row.addWidget(self.button("Entfernen ❌", self.remove_selected_queue))
        row.addWidget(self.button("Leeren 🧹", self.clear_queue))
        lay.addLayout(row)
        tabs.addTab(page, "Warteschlange")

        # Playlists
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        row = QHBoxLayout()
        self.playlist_combo = QComboBox()
        self.playlist_combo.currentTextChanged.connect(self.update_playlist_songs_list)
        row.addWidget(self.playlist_combo)
        for text, slot, tip in (("＋", self.create_playlist_ui, "Neue Playlist"),
                                ("🗑️", self.delete_selected_playlist_ui, "Playlist löschen")):
            b = self.button(text, slot, tip)
            b.setFixedWidth(35)
            row.addWidget(b)
        lay.addLayout(row)
        self.playlist_songs_list = QListWidget()
        self.playlist_songs_list.itemDoubleClicked.connect(lambda it: self.play_song(it.data(SONG_ROLE)))
        self.playlist_songs_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_songs_list.customContextMenuRequested.connect(
            lambda pos: self.show_song_list_menu(self.playlist_songs_list, pos))
        lay.addWidget(self.playlist_songs_list)
        row = QHBoxLayout()
        row.addWidget(self.button("Alle in Warteschlange 🎵", self.add_playlist_to_queue))
        row.addWidget(self.button("Entfernen ❌", self.remove_selected_playlist_song))
        lay.addLayout(row)
        tabs.addTab(page, "Playlists")

        # Verlauf
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 10, 10, 10)
        self.history_filter = QLineEdit()
        self.history_filter.setPlaceholderText("Im Verlauf suchen …")
        self.history_filter.textChanged.connect(self.update_history_ui)
        lay.addWidget(self.history_filter)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(lambda it: self.play_song(it.data(SONG_ROLE)))
        self.history_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(
            lambda pos: self.show_song_list_menu(self.history_list, pos))
        lay.addWidget(self.history_list)
        row = QHBoxLayout()
        row.addWidget(self.button("In Playlist … 💾",
                                  lambda: self.add_list_selection_to_playlist(self.history_list)))
        row.addWidget(self.button("Verlauf leeren 🧹", self.clear_history))
        lay.addLayout(row)
        tabs.addTab(page, "Verlauf")
        return tabs

    def build_player_panel(self):
        frame = QFrame()
        frame.setObjectName("control_panel")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(15, 10, 15, 10)
        lay.setSpacing(15)

        info = QVBoxLayout()
        info.setSpacing(2)
        self.track_title = QLabel("Nichts läuft")
        self.track_title.setObjectName("song_title_label")
        self.track_title.setWordWrap(True)
        self.track_title.setMaximumWidth(320)
        self.track_channel = QLabel("–")
        self.track_channel.setObjectName("song_channel_label")
        info.addWidget(self.track_title)
        info.addWidget(self.track_channel)
        lay.addLayout(info, 2)

        center = QVBoxLayout()
        center.setSpacing(4)
        buttons = QHBoxLayout()
        buttons.setAlignment(Qt.AlignmentFlag.AlignCenter)
        buttons.setSpacing(10)
        for name, text, tip, slot in (
                ("media_prev", "⏮️", "Vorheriger Titel", self.play_previous_song),
                ("media_play", "▶️", "Abspielen", self.play_song_action),
                ("media_pause", "⏸️", "Pause", self.pause_song_action),
                ("media_stop", "⏹️", "Stopp", self.stop_song_action),
                ("media_next", "⏭️", "Nächster Titel", self.skip_song)):
            b = self.button(text, slot, tip, name)
            b.setFixedSize(80, 48)
            buttons.addWidget(b)
        center.addLayout(buttons)

        row = QHBoxLayout()
        self.lbl_time_current = QLabel("00:00")
        self.lbl_time_current.setFixedWidth(52)
        self.lbl_time_current.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderPressed.connect(self.on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self.on_slider_released)
        self.lbl_time_total = QLabel("00:00")
        self.lbl_time_total.setFixedWidth(52)
        row.addWidget(self.lbl_time_current)
        row.addWidget(self.progress_slider)
        row.addWidget(self.lbl_time_total)
        center.addLayout(row)
        lay.addLayout(center, 5)

        right = QVBoxLayout()
        right.setSpacing(4)
        row = QHBoxLayout()
        self.autoplay_cb = QCheckBox("Dauerradio 📻")
        self.autoplay_cb.setToolTip("Spielt immer weiter; ist die Liste durch, startet eine neue Zufallssuche")
        row.addWidget(self.autoplay_cb)
        row.addWidget(self.button("Im Browser 🌐", self.open_current_in_browser,
                                  "Aktuellen Titel auf YouTube öffnen"))
        row.addWidget(self.button("Merken 💾", self.add_current_song_to_playlist_dialog,
                                  "Aktuellen Titel in eine Playlist legen"))
        right.addLayout(row)

        row = QHBoxLayout()
        row.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(QLabel("🔊"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.valueChanged.connect(self.set_player_volume)
        row.addWidget(self.volume_slider)
        right.addLayout(row)
        lay.addLayout(right, 3)
        return frame

    # --- Einstellungen ---

    def apply_settings(self):
        s = self.settings
        self.max_views_spin.setValue(s.get("max_views", 300_000))
        self.min_views_spin.setValue(s.get("min_views", 50))
        self.min_dur_spin.setValue(s.get("min_dur", 2))
        self.max_dur_spin.setValue(s.get("max_dur", 15))
        self.results_count_spin.setValue(s.get("results", 60))
        self.hide_heard_cb.setChecked(s.get("hide_heard", True))
        self.exclude_cb.setChecked(s.get("exclude", True))
        self.autoplay_cb.setChecked(s.get("autoplay", True))
        self.volume_slider.setValue(s.get("volume", 80))
        self.search_input.setText(s.get("last_query", ""))
        self.connect_filter_widgets()

    def store_settings(self):
        storage.save_settings({
            "max_views": self.max_views_spin.value(),
            "min_views": self.min_views_spin.value(),
            "min_dur": self.min_dur_spin.value(),
            "max_dur": self.max_dur_spin.value(),
            "results": self.results_count_spin.value(),
            "hide_heard": self.hide_heard_cb.isChecked(),
            "exclude": self.exclude_cb.isChecked(),
            "autoplay": self.autoplay_cb.isChecked(),
            "volume": self.volume_slider.value(),
            "last_query": self.search_input.text().strip(),
        })

    def edit_terms(self):
        dlg = TermsDialog(self.terms, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.terms = dlg.terms()
            qg.save_terms(self.terms)
            self.exclude_re = qg.build_exclude_matcher(self.terms["ausschluss"])
            self.filter_and_display_results()
            self.status_label.setText("Begriffe gespeichert.")

    # --- Genre & Zufall ---

    def explain_genre(self):
        term = self.search_input.text().strip()
        if not term:
            self.status_label.setText("Erst einen Suchbegriff eingeben.")
            return
        self.status_label.setText("Hole Erklärung …")
        self.what_is_this_btn.setEnabled(False)
        self.info_worker = GenreInfoWorker(term, self.terms, self)
        self.info_worker.finished_signal.connect(self.on_genre_info_finished)
        self.info_worker.error_signal.connect(self.on_genre_info_error)
        self.info_worker.start()

    def on_genre_info_finished(self, genre, explanation):
        self.what_is_this_btn.setEnabled(True)
        self.status_label.setText("")
        GenreInfoDialog(genre, explanation, self).exec()

    def on_genre_info_error(self, msg):
        self.what_is_this_btn.setEnabled(True)
        self.status_label.setText(f"Erklärung fehlgeschlagen: {msg}")

    def roll_vibe(self):
        genre = random.choice(self.terms["genres"] or qg.DEFAULT_GENRES)
        self.search_input.setText(genre)
        self.status_label.setText(f"Gewürfelt: {genre}")

    def trigger_surprise(self):
        self.search_input.setText(qg.generate_random_query(self.terms))
        self.start_youtube_search()

    # --- Suche ---

    def start_youtube_search(self):
        query = self.search_input.text().strip()
        if not query:
            query = qg.generate_random_query(self.terms)
            self.search_input.setText(query)
        self.autoplay_attempts = 0
        self.launch_search(query, self.on_search_finished, self.on_search_error)

    def launch_search(self, query, on_finished, on_error):
        self.search_generation += 1
        generation = self.search_generation
        self.status_label.setText(f"Suche „{query}“ …")
        self.search_btn.setText("Suche läuft … ⏳")
        worker = SearchWorker(query, self.results_count_spin.value())
        self.active_workers.add(worker)

        def finished(results):
            if generation == self.search_generation:
                self.search_btn.setText("Suchen 🔍")
                on_finished(results)

        def error(msg):
            if generation == self.search_generation:
                self.search_btn.setText("Suchen 🔍")
                on_error(msg)

        worker.finished_signal.connect(finished)
        worker.error_signal.connect(error)
        worker.finished.connect(lambda: self.active_workers.discard(worker))
        worker.start()

    def on_search_finished(self, results):
        self.search_results = results
        self.filter_and_display_results(autostart=True)

    def on_search_error(self, msg):
        self.status_label.setText("Suche fehlgeschlagen.")
        QMessageBox.warning(self, "Suche fehlgeschlagen", msg)

    def filter_results(self):
        """Wendet alle Filter an. Gibt (Treffer, Zähler je Ausschlussgrund) zurück."""
        min_v, max_v = self.min_views_spin.value(), self.max_views_spin.value()
        min_s, max_s = self.min_dur_spin.value() * 60, self.max_dur_spin.value() * 60
        hide_heard = self.hide_heard_cb.isChecked()
        exclude = self.exclude_re if self.exclude_cb.isChecked() else None

        kept = []
        reasons = {"Aufrufe": 0, "Länge": 0, "Nicht-Musik": 0, "schon gehört": 0}
        for r in self.search_results:
            if not min_v <= r["view_count"] <= max_v:
                reasons["Aufrufe"] += 1
            elif not min_s <= r["duration"] <= max_s:
                reasons["Länge"] += 1
            elif exclude and exclude.search(r["title"]):
                reasons["Nicht-Musik"] += 1
            elif r["id"] in self.session_played or (hide_heard and r["id"] in self.history):
                reasons["schon gehört"] += 1
            else:
                kept.append(r)
        return kept, reasons

    def filter_and_display_results(self, autostart=False):
        self.filtered_results, reasons = self.filter_results()

        t = self.results_table
        t.setSortingEnabled(False)
        t.setRowCount(len(self.filtered_results))
        for i, song in enumerate(self.filtered_results):
            cells = (
                (song["title"], song["title"].lower()),
                (song["channel"], song["channel"].lower()),
                (fmt_views(song["view_count"]), song["view_count"]),
                (song["duration_string"], song["duration"]),
            )
            for col, (text, key) in enumerate(cells):
                item = SortItem(text)
                item.setData(Qt.ItemDataRole.UserRole, key)
                if col == 0:
                    item.setData(SONG_ROLE, song)
                    item.setToolTip(text)
                t.setItem(i, col, item)
        t.setSortingEnabled(True)

        if self.search_results:
            hidden = ", ".join(f"{n}× {why}" for why, n in reasons.items() if n)
            self.filter_info.setText(
                f"{len(self.filtered_results)} von {len(self.search_results)} Treffern"
                + (f" · ausgeblendet: {hidden}" if hidden else ""))
            if self.filtered_results:
                self.status_label.setText(f"{len(self.filtered_results)} Titel gefunden.")
            else:
                self.status_label.setText("Alles ausgefiltert – Filter lockern oder anders suchen.")
        elif autostart:
            self.filter_info.setText("")
            self.status_label.setText("YouTube hat nichts gefunden.")

        if autostart and self.autoplay_cb.isChecked() and self.player.process is None \
                and self.filtered_results:
            self.play_next_autoplay()

    # --- Treffer ---

    def get_selected_result_song(self):
        row = self.results_table.currentRow()
        item = self.results_table.item(row, 0) if row >= 0 else None
        return item.data(SONG_ROLE) if item else None

    def play_selected_result(self):
        song = self.get_selected_result_song()
        if song:
            self.play_song(song)
        else:
            self.status_label.setText("Kein Titel ausgewählt.")

    def enqueue(self, song):
        self.queue.append(song)
        self.queue_list.addItem(song_item(song))
        self.status_label.setText(f"In der Warteschlange: {song['title']}")

    def add_selected_to_queue(self):
        song = self.get_selected_result_song()
        if song:
            self.enqueue(song)

    def show_results_context_menu(self, pos):
        item = self.results_table.itemAt(pos)
        if item:
            song = self.results_table.item(item.row(), 0).data(SONG_ROLE)
            self.song_menu(song).exec(self.results_table.viewport().mapToGlobal(pos))

    def show_song_list_menu(self, widget, pos):
        item = widget.itemAt(pos)
        if item:
            self.song_menu(item.data(SONG_ROLE)).exec(widget.viewport().mapToGlobal(pos))

    def song_menu(self, song):
        menu = QMenu(self)
        menu.addAction("▶️ Abspielen", lambda: self.play_song(song))
        menu.addAction("➕ In Warteschlange", lambda: self.enqueue(song))
        menu.addMenu(self.playlist_menu(song, menu))
        menu.addSeparator()
        menu.addAction("🌐 Im Browser öffnen", lambda: open_url(song["url"]))
        menu.addAction("🔍 Mehr von diesem Kanal", lambda: self.search_channel(song))
        return menu

    def search_channel(self, song):
        self.search_input.setText(song["channel"])
        self.start_youtube_search()

    # --- Warteschlange ---

    def play_selected_queue(self):
        row = self.queue_list.currentRow()
        if 0 <= row < len(self.queue):
            self.queue_list.takeItem(row)
            self.play_song(self.queue.pop(row))

    def remove_selected_queue(self):
        row = self.queue_list.currentRow()
        if 0 <= row < len(self.queue):
            self.queue.pop(row)
            self.queue_list.takeItem(row)

    def clear_queue(self):
        self.queue.clear()
        self.queue_list.clear()

    # --- Wiedergabe ---

    def play_song(self, song, add_to_history=True):
        if not song:
            return
        current = self.player.current_song
        if add_to_history and current and current["id"] != song["id"]:
            self.playback_history.append(current)

        self.track_title.setText(song["title"])
        self.track_channel.setText(f"{song['channel']} • {fmt_views(song.get('view_count') or 0)} Aufrufe")
        self.status_label.setText(f"Spielt: {song['title']}")
        self.session_played.add(song["id"])
        self.history.add(song)
        self.update_history_ui()

        self.player.start(song["url"], song, volume=self.volume_slider.value())
        self.last_paused = None
        self.mpris.update(song=song, status="Playing", duration=song.get("duration") or 0, position=0)

        self.progress_slider.setValue(0)
        self.lbl_time_current.setText("00:00")
        self.lbl_time_total.setText(song.get("duration_string") or "00:00")
        self.highlight_song_in_table(song["id"])

    def highlight_song_in_table(self, song_id):
        t = self.results_table
        for row in range(t.rowCount()):
            item = t.item(row, 0)
            if item and (item.data(SONG_ROLE) or {}).get("id") == song_id:
                t.selectRow(row)
                t.scrollToItem(item)
                return

    def play_previous_song(self):
        if not self.playback_history:
            self.status_label.setText("Kein vorheriger Titel.")
            return
        prev = self.playback_history.pop()
        current = self.player.current_song
        if current:
            # Aktuellen Titel vorn einreihen, damit ⏭️ wieder dorthin führt
            self.queue.insert(0, current)
            self.queue_list.insertItem(0, song_item(current))
        self.play_song(prev, add_to_history=False)

    def play_song_action(self):
        if self.player.process is not None:
            self.player.resume()
        elif self.queue:
            row = self.queue_list.currentRow()
            idx = row if 0 <= row < len(self.queue) else 0
            self.queue_list.takeItem(idx)
            self.play_song(self.queue.pop(idx))
        elif self.filtered_results:
            self.play_song(self.get_selected_result_song() or random.choice(self.filtered_results))
        else:
            self.trigger_surprise()

    def pause_song_action(self):
        if self.player.process is not None:
            self.player.pause()

    def toggle_pause_action(self):
        if self.player.process is not None:
            self.player.toggle_pause()
        else:
            self.play_song_action()

    def reset_player_display(self, status):
        self.track_title.setText("Nichts läuft")
        self.track_channel.setText("–")
        self.lbl_time_current.setText("00:00")
        self.lbl_time_total.setText("00:00")
        self.progress_slider.setValue(0)
        self.status_label.setText(status)
        self.mpris.update(song=None, status="Stopped", duration=0, position=0)

    def stop_song_action(self):
        self.player.stop()
        self.reset_player_display("Gestoppt.")

    def skip_song(self):
        self.player.stop()
        self.handle_track_end()

    def handle_track_end(self):
        self.player.stop()
        if self.queue:
            self.queue_list.takeItem(0)
            self.play_song(self.queue.pop(0))
        elif self.autoplay_cb.isChecked():
            self.play_next_autoplay()
        else:
            self.reset_player_display("Wiedergabe beendet.")

    def play_next_autoplay(self):
        candidates = [r for r in self.filtered_results if r["id"] not in self.session_played]
        if candidates:
            self.autoplay_attempts = 0
            self.play_song(random.choice(candidates))
        elif self.autoplay_attempts < 5:
            self.autoplay_attempts += 1
            query = qg.generate_random_query(self.terms)
            self.search_input.setText(query)
            self.launch_search(query, self.on_autoplay_search_finished, self.on_autoplay_search_error)
        else:
            self.autoplay_attempts = 0
            self.reset_player_display("Dauerradio gestoppt: fünf Suchen ohne passenden Titel.")

    def on_autoplay_search_finished(self, results):
        self.search_results = results
        self.filter_and_display_results()
        if self.player.process is None:
            self.play_next_autoplay()   # spielt oder sucht erneut

    def on_autoplay_search_error(self, msg):
        self.status_label.setText(f"Suche fehlgeschlagen ({msg[:60]}), versuche nächste …")
        self.play_next_autoplay()

    # --- Status-Abfrage ---

    def update_player_status(self):
        if self.player.process is None:
            return
        if self.player.process.poll() is not None:
            self.handle_track_end()
            return
        pos, dur, paused = self.player.get_position()
        self.mpris.state["position"] = pos
        if paused != self.last_paused:
            self.last_paused = paused
            self.mpris.update(status="Paused" if paused else "Playing")
        if dur > 0 and abs(dur - self.mpris.state["duration"]) > 1:
            self.mpris.update(duration=dur)
        if dur > 0 and not self.is_user_seeking:
            self.progress_slider.setMaximum(int(dur))
            self.progress_slider.setValue(int(pos))
            self.lbl_time_current.setText(self.format_time(pos))
            self.lbl_time_total.setText(self.format_time(dur))

    @staticmethod
    def format_time(seconds):
        seconds = int(seconds)
        h, rest = divmod(seconds, 3600)
        m, s = divmod(rest, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def on_slider_pressed(self):
        self.is_user_seeking = True

    def on_slider_released(self):
        if self.player.process is not None:
            self.player.seek(self.progress_slider.value())
            self.mpris.seeked(self.progress_slider.value())
        self.is_user_seeking = False

    def set_player_volume(self, value):
        self.player.set_volume(value)
        self.mpris.update(volume=value)

    def open_current_in_browser(self):
        if self.player.current_song:
            open_url(self.player.current_song["url"])
        else:
            self.status_label.setText("Gerade läuft nichts.")

    def bring_to_front(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # --- Verlauf ---

    def update_history_ui(self, *_):
        needle = self.history_filter.text().strip().lower()
        self.history_list.clear()
        shown = 0
        for e in reversed(self.history.entries):
            if needle and needle not in f"{e.get('title', '')} {e.get('channel', '')}".lower():
                continue
            when = (e.get("gehoert_am") or "")[5:]   # "MM-TT hh:mm"
            self.history_list.addItem(song_item(e, f"{when}  {song_label(e)}"))
            shown += 1
            if shown >= 500:
                break

    def clear_history(self):
        if QMessageBox.question(
                self, "Verlauf leeren",
                f"Alle {len(self.history.entries)} Einträge löschen? Danach können "
                "schon gehörte Titel wieder auftauchen.") == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.update_history_ui()
            self.filter_and_display_results()

    # --- Playlists ---

    def save_playlists(self):
        storage.save_playlists(self.playlists)

    def update_playlists_ui(self):
        current = self.playlist_combo.currentText()
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        self.playlist_combo.addItems(sorted(self.playlists))
        if current in self.playlists:
            self.playlist_combo.setCurrentText(current)
        self.playlist_combo.blockSignals(False)
        self.update_playlist_songs_list()

    def update_playlist_songs_list(self, *_):
        self.playlist_songs_list.clear()
        for s in self.playlists.get(self.playlist_combo.currentText(), []):
            self.playlist_songs_list.addItem(song_item(s))

    def ask_playlist_name(self):
        name, ok = QInputDialog.getText(self, "Neue Playlist", "Name der Playlist:")
        return name.strip() if ok and name.strip() else None

    def create_playlist_ui(self):
        name = self.ask_playlist_name()
        if not name:
            return
        if name in self.playlists:
            QMessageBox.information(self, "Playlist", "Diese Playlist gibt es schon.")
            return
        self.playlists[name] = []
        self.save_playlists()
        self.update_playlists_ui()
        self.playlist_combo.setCurrentText(name)

    def delete_selected_playlist_ui(self):
        current = self.playlist_combo.currentText()
        if current and QMessageBox.question(
                self, "Playlist löschen",
                f"Playlist „{current}“ wirklich löschen?") == QMessageBox.StandardButton.Yes:
            self.playlists.pop(current, None)
            self.save_playlists()
            self.update_playlists_ui()

    def add_playlist_to_queue(self):
        songs = self.playlists.get(self.playlist_combo.currentText(), [])
        for s in songs:
            self.enqueue(s)
        self.status_label.setText(f"{len(songs)} Titel in die Warteschlange gelegt.")

    def remove_selected_playlist_song(self):
        row = self.playlist_songs_list.currentRow()
        songs = self.playlists.get(self.playlist_combo.currentText())
        if songs is not None and 0 <= row < len(songs):
            songs.pop(row)
            self.save_playlists()
            self.update_playlist_songs_list()

    def playlist_menu(self, song, parent=None):
        menu = QMenu("💾 In Playlist", parent or self)
        for name in sorted(self.playlists):
            menu.addAction(name, lambda n=name: self.add_song_to_playlist(song, n))
        if self.playlists:
            menu.addSeparator()
        menu.addAction("＋ Neue Playlist …", lambda: self.create_playlist_and_add_song(song))
        return menu

    def add_selected_result_to_playlist_dialog(self):
        song = self.get_selected_result_song()
        if song:
            self.playlist_menu(song).exec(self.cursor().pos())
        else:
            self.status_label.setText("Kein Titel ausgewählt.")

    def add_list_selection_to_playlist(self, widget):
        item = widget.currentItem()
        if item:
            self.playlist_menu(item.data(SONG_ROLE)).exec(self.cursor().pos())

    def add_current_song_to_playlist_dialog(self):
        if self.player.current_song:
            self.playlist_menu(self.player.current_song).exec(self.cursor().pos())
        else:
            self.status_label.setText("Gerade läuft nichts.")

    def add_song_to_playlist(self, song, name):
        songs = self.playlists.setdefault(name, [])
        if any(s["id"] == song["id"] for s in songs):
            self.status_label.setText(f"Schon in „{name}“.")
            return
        songs.append({k: song.get(k) for k in SONG_KEYS})
        self.save_playlists()
        self.update_playlist_songs_list()
        self.status_label.setText(f"In „{name}“ gemerkt: {song['title']}")

    def create_playlist_and_add_song(self, song):
        name = self.ask_playlist_name()
        if name:
            self.add_song_to_playlist(song, name)
            self.update_playlists_ui()
            self.playlist_combo.setCurrentText(name)

    def closeEvent(self, event):
        self.store_settings()
        self.player.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Wayland/Hyprland ordnet Fenster über die app_id dem .desktop-Eintrag zu (Icon, Name).
    app.setDesktopFileName("youtube-random-music")
    app.setApplicationName("youtube-random-music")
    window = YoutubeMusicZentrale()
    window.show()
    sys.exit(app.exec())
