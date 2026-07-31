"""
Settings page — single QFormLayout so every combo shares the same column width.
Section headers replace QGroupBox titles.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QFormLayout, QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt

from database.database import Database


def _section_header(text: str) -> QLabel:
    """Styled section header matching the old QGroupBox title look."""
    lbl = QLabel(text)
    lbl.setStyleSheet(
        "font-weight: 600; color: #495057; font-size: 13px;"
        "padding-top: 18px; padding-bottom: 4px;"
    )
    return lbl


def _separator() -> QFrame:
    """Horizontal line between sections."""
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    line.setStyleSheet("color: #e9ecef; margin-top: 2px; margin-bottom: 6px;")
    return line


class SettingsWidget(QWidget):
    """All fields in one QFormLayout — uniform column width."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._init_ui()
        self._load_settings()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(0)

        title = QLabel("Settings")
        title.setStyleSheet("font-size: 22px; font-weight: 600; padding-bottom: 12px;")
        layout.addWidget(title)

        # ── Single form for everything ────────────────────────────────
        form = QFormLayout()
        form.setSpacing(10)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        # === Timer Defaults ===
        layout.addWidget(_section_header("Timer Defaults"))
        layout.addWidget(_separator())

        self._focus_combo = QComboBox()
        for label, val in [("25 min", 25), ("50 min", 50), ("90 min", 90),
                           ("120 min", 120), ("180 min", 180)]:
            self._focus_combo.addItem(label, val)
        form.addRow("Default focus duration:", self._focus_combo)

        self._break_combo = QComboBox()
        for label, val in [("5 min", 5), ("10 min", 10), ("15 min", 15),
                           ("20 min", 20), ("30 min", 30)]:
            self._break_combo.addItem(label, val)
        form.addRow("Default break duration:", self._break_combo)

        self._cycles_combo = QComboBox()
        for c in [1, 2, 3, 4, 5, 6, 8, 10, 12]:
            self._cycles_combo.addItem(str(c), c)
        form.addRow("Pomodoro cycles:", self._cycles_combo)

        self._goal_combo = QComboBox()
        for label, val in [("30 min", 30), ("1 hour", 60), ("2 hours", 120),
                           ("3 hours", 180), ("4 hours", 240), ("6 hours", 360),
                           ("8 hours", 480), ("10 hours", 600), ("12 hours", 720)]:
            self._goal_combo.addItem(label, val)
        form.addRow("Daily focus goal:", self._goal_combo)

        layout.addLayout(form)

        # === Appearance ===
        layout.addWidget(_section_header("Appearance"))
        layout.addWidget(_separator())

        form2 = QFormLayout()
        form2.setSpacing(10)
        form2.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._theme_combo = QComboBox()
        self._theme_combo.addItem("Light", "light")
        self._theme_combo.addItem("Dark", "dark")
        form2.addRow("Theme:", self._theme_combo)
        layout.addLayout(form2)

        # === Quotes ===
        layout.addWidget(_section_header("Quotes"))
        layout.addWidget(_separator())

        form3 = QFormLayout()
        form3.setSpacing(10)
        form3.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._quote_freq_combo = QComboBox()
        self._quote_freq_combo.addItem("Per session", "per_session")
        self._quote_freq_combo.addItem("Per break", "per_break")
        self._quote_freq_combo.addItem("Daily", "daily")
        form3.addRow("Quote change frequency:", self._quote_freq_combo)
        layout.addLayout(form3)

        # === Audio Defaults ===
        layout.addWidget(_section_header("Audio Defaults"))
        layout.addWidget(_separator())

        form4 = QFormLayout()
        form4.setSpacing(10)
        form4.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._music_vol_combo = QComboBox()
        for v in range(0, 101, 10):
            self._music_vol_combo.addItem(f"{v}%", v)
        form4.addRow("Default music volume:", self._music_vol_combo)

        self._ambient_vol_combo = QComboBox()
        for v in range(0, 101, 10):
            self._ambient_vol_combo.addItem(f"{v}%", v)
        form4.addRow("Default ambient volume:", self._ambient_vol_combo)
        layout.addLayout(form4)

        # === Startup ===
        layout.addWidget(_section_header("Startup"))
        layout.addWidget(_separator())

        form5 = QFormLayout()
        form5.setSpacing(10)
        form5.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        self._startup_combo = QComboBox()
        self._startup_combo.addItem("Timer", "timer")
        self._startup_combo.addItem("Statistics", "statistics")
        self._startup_combo.addItem("History", "history")
        form5.addRow("Default page on launch:", self._startup_combo)
        layout.addLayout(form5)

        # ── Save ──────────────────────────────────────────────────────
        layout.addSpacing(20)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)
        layout.addStretch()

        # ── Collect all combos for post-layout width sync ─────────────
        self._all_combos = [
            self._focus_combo, self._break_combo, self._cycles_combo,
            self._goal_combo, self._theme_combo, self._quote_freq_combo,
            self._music_vol_combo, self._ambient_vol_combo, self._startup_combo,
        ]

    def showEvent(self, event) -> None:
        """After first layout, sync all combo widths to the widest one."""
        super().showEvent(event)
        max_w = max(c.sizeHint().width() for c in self._all_combos)
        for c in self._all_combos:
            c.setMinimumWidth(max_w + 8)

    # ── Load / Save ───────────────────────────────────────────────────

    @staticmethod
    def _select_by_data(combo: QComboBox, value: int) -> None:
        for i in range(combo.count()):
            if combo.itemData(i) == value:
                combo.setCurrentIndex(i)
                return

    def _load_settings(self) -> None:
        self._select_by_data(self._focus_combo,
                             int(self._db.get_setting("focus_minutes", "25")))
        self._select_by_data(self._break_combo,
                             int(self._db.get_setting("break_minutes", "5")))
        self._select_by_data(self._cycles_combo,
                             int(self._db.get_setting("pomodoro_cycles", "4")))
        self._select_by_data(self._goal_combo,
                             int(self._db.get_setting("daily_goal_minutes", "240")))

        theme = self._db.get_setting("theme", "light")
        idx = self._theme_combo.findData(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

        freq = self._db.get_setting("quote_frequency", "per_session")
        idx = self._quote_freq_combo.findData(freq)
        if idx >= 0:
            self._quote_freq_combo.setCurrentIndex(idx)

        self._select_by_data(self._music_vol_combo,
                             int(self._db.get_setting("music_volume", "40")))
        self._select_by_data(self._ambient_vol_combo,
                             int(self._db.get_setting("ambient_volume", "30")))

        startup = self._db.get_setting("startup_behavior", "timer")
        idx = self._startup_combo.findData(startup)
        if idx >= 0:
            self._startup_combo.setCurrentIndex(idx)

    def _save_settings(self) -> None:
        self._db.set_setting("focus_minutes", str(self._focus_combo.currentData()))
        self._db.set_setting("break_minutes", str(self._break_combo.currentData()))
        self._db.set_setting("pomodoro_cycles", str(self._cycles_combo.currentData()))
        self._db.set_setting("daily_goal_minutes", str(self._goal_combo.currentData()))
        self._db.set_setting("theme", self._theme_combo.currentData())
        self._db.set_setting("quote_frequency", self._quote_freq_combo.currentData())
        self._db.set_setting("music_volume", str(self._music_vol_combo.currentData()))
        self._db.set_setting("ambient_volume", str(self._ambient_vol_combo.currentData()))
        self._db.set_setting("startup_behavior", self._startup_combo.currentData())

        QMessageBox.information(
            self, "Settings Saved",
            "Settings have been saved successfully.\n"
            "Theme changes will take effect after restarting the application."
        )

    def refresh_on_navigate(self) -> None:
        self._load_settings()
