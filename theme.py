# Dunkles Farbschema (Qt-Stylesheet)
QSS_THEME = """
QWidget {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Noto Sans', 'DejaVu Sans', sans-serif;
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
