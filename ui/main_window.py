"""
Main application window with sidebar navigation and stacked page container.
Integrates all UI pages and core components (timer, music player, database).
"""

from datetime import datetime, timedelta
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel,
    QApplication,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon

import pygame

from config.settings import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, SIDEBAR_WIDTH,
)
from core.timer import TimerState, FocusTimer, PomodoroPhase
from core.music_player import MusicPlayer
from database.database import Database
from sounds.generator import get_sound_path, generate_completion_chime
from ui.styles import get_stylesheet
from ui.timer_widget import TimerWidget
from ui.statistics_widget import StatisticsWidget
from ui.history_widget import HistoryWidget
from ui.quotes_widget import QuotesWidget
from ui.music_widget import MusicWidget
from ui.settings_widget import SettingsWidget


NAV_ITEMS = [
    ("⏱  Timer", "timer"),
    ("📊  Statistics", "statistics"),
    ("📋  History", "history"),
    ("💬  Quotes", "quotes"),
    ("🎵  Music", "music"),
    ("⚙  Settings", "settings"),
]


class MainWindow(QMainWindow):
    """Top-level window containing sidebar and stacked pages."""

    def __init__(self, app: QApplication):
        super().__init__()
        self._app = app

        # ── Core components ───────────────────────────────────────────
        self._db = Database()
        self._timer = FocusTimer(self)
        self._music_player = MusicPlayer()

        # ── Window setup ──────────────────────────────────────────────
        self.setWindowTitle(APP_NAME)
        self._set_app_icon()
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        # Apply theme
        theme = self._db.get_setting("theme", "light")
        self._app.setStyleSheet(get_stylesheet(theme))

        # ── Build UI ──────────────────────────────────────────────────
        self._nav_buttons: dict[str, QPushButton] = {}
        self._pages: dict[str, QWidget] = {}
        self._init_central_widget()
        self._init_pages()
        self._connect_global_signals()

        # Generate completion chime and ambient sounds if missing
        self._ensure_assets()

        # Navigate to default startup page
        startup = self._db.get_setting("startup_behavior", "timer")
        self._navigate_to(startup)

        # Pygame event polling timer (for music end-of-track events)
        self._pygame_timer = QTimer(self)
        self._pygame_timer.timeout.connect(self._poll_pygame_events)
        self._pygame_timer.start(200)  # poll every 200ms

    # ── Central widget with sidebar + pages ───────────────────────────

    def _init_central_widget(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 16, 0, 16)
        sidebar_layout.setSpacing(2)

        # App title in sidebar
        app_label = QLabel(APP_NAME)
        app_label.setStyleSheet(
            "font-size: 18px; font-weight: 700; padding: 12px 16px 20px 16px;"
        )
        sidebar_layout.addWidget(app_label)

        # Navigation buttons
        btn_group = []
        for label, key in NAV_ITEMS:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self._navigate_to(k))
            sidebar_layout.addWidget(btn)
            self._nav_buttons[key] = btn
            btn_group.append(btn)

        sidebar_layout.addStretch()

        # Version label
        version_lbl = QLabel("v1.0.0")
        version_lbl.setObjectName("sidebarLabel")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(version_lbl)

        root.addWidget(sidebar)

        # Page container
        self._stack = QStackedWidget()
        self._stack.setObjectName("pageContainer")
        root.addWidget(self._stack, 1)

    # ── Page initialization ───────────────────────────────────────────

    def _init_pages(self) -> None:
        """Create all page widgets and add them to the stack."""

        # Timer page
        timer_page = TimerWidget(self._timer, self._db)
        timer_page.session_completed.connect(self._on_session_completed)
        self._pages["timer"] = timer_page
        self._stack.addWidget(timer_page)

        # Statistics page
        stats_page = StatisticsWidget(self._db)
        self._pages["statistics"] = stats_page
        self._stack.addWidget(stats_page)

        # History page
        history_page = HistoryWidget(self._db)
        self._pages["history"] = history_page
        self._stack.addWidget(history_page)

        # Quotes page
        quotes_page = QuotesWidget(self._db)
        self._pages["quotes"] = quotes_page
        self._stack.addWidget(quotes_page)

        # Music page
        music_page = MusicWidget(self._music_player, self._db)
        self._pages["music"] = music_page
        self._stack.addWidget(music_page)

        # Settings page
        settings_page = SettingsWidget(self._db)
        self._pages["settings"] = settings_page
        self._stack.addWidget(settings_page)

    # ── Navigation ────────────────────────────────────────────────────

    def _navigate_to(self, key: str) -> None:
        """Switch to the page identified by key."""
        page = self._pages.get(key)
        if page is None:
            return

        self._stack.setCurrentWidget(page)

        # Update button states
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)

        # Call refresh hook if the page has one
        if hasattr(page, "refresh_on_navigate"):
            page.refresh_on_navigate()

    # ── Global signal connections ─────────────────────────────────────

    def _connect_global_signals(self) -> None:
        """Connect timer signals that affect multiple pages."""
        # When a focus session finishes in Pomodoro, play the chime
        self._timer.finished.connect(self._play_completion_chime)

    def _on_session_completed(self, duration_seconds: int, task_desc: str) -> None:
        """Save a completed focus session to the database."""
        now = datetime.now()
        self._db.save_session(
            session_date=now.date(),
            start_time=(now - timedelta(seconds=duration_seconds)).strftime("%H:%M"),
            duration_seconds=duration_seconds,
            task_desc=task_desc,
            completed=True,
        )

    # ── Pygame event loop integration ─────────────────────────────────

    def _poll_pygame_events(self) -> None:
        """Process pygame events (e.g., music track-end) in the Qt event loop."""
        try:
            for event in pygame.event.get():
                self._music_player.process_events(event)
        except pygame.error:
            pass  # pygame not fully initialized — non-fatal

    # ── Assets ────────────────────────────────────────────────────────

    def _set_app_icon(self) -> None:
        """Load the application icon from assets/icon.ico."""
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icon.ico",
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _ensure_assets(self) -> None:
        """Generate the completion chime if not present."""
        chime_path = get_sound_path("__completion_chime")
        if not os.path.exists(chime_path):
            try:
                generate_completion_chime(chime_path)
            except Exception:
                pass  # Non-critical; we'll just skip the sound

    def _play_completion_chime(self) -> None:
        """Play a short notification sound when a session finishes."""
        chime_path = get_sound_path("__completion_chime")
        if os.path.exists(chime_path):
            try:
                sound = pygame.mixer.Sound(chime_path)
                sound.set_volume(0.5)
                sound.play()
            except pygame.error:
                pass  # Audio unavailable, ignore

    # ── Cleanup ───────────────────────────────────────────────────────

    def closeEvent(self, event) -> None:
        """Ensure clean shutdown."""
        self._pygame_timer.stop()
        self._music_player.shutdown()
        self._db.close()
        super().closeEvent(event)
