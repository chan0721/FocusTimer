"""
Main timer page — countdown display, duration selection, Pomodoro toggles,
daily progress bar, inspirational quotes, and task description input.
"""

import random
from datetime import datetime, date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QSpinBox,
    QProgressBar, QCheckBox, QGroupBox, QGridLayout,
    QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from config.settings import FOCUS_PRESETS
from core.timer import TimerState, PomodoroPhase, FocusTimer
from database.database import Database


class TimerWidget(QWidget):
    """The main focus timer view with all controls."""

    # Emitted when a focus session is completed (so MainWindow can save it)
    session_completed = pyqtSignal(int, str)  # duration_seconds, task_desc

    def __init__(self, timer: FocusTimer, db: Database, parent=None):
        super().__init__(parent)
        self._timer = timer
        self._db = db
        self._current_quote: tuple[str, str] = ("", "")
        self._init_ui()
        self._connect_signals()
        self._refresh_quote()

    # ── Build UI ──────────────────────────────────────────────────────

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 36, 48, 36)
        layout.setSpacing(16)

        # ── Phase label (Focus / Break) ───────────────────────────────
        self._phase_label = QLabel("")
        self._phase_label.setObjectName("phaseLabel")
        self._phase_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_label.setVisible(False)
        layout.addWidget(self._phase_label)

        # ── Countdown display ─────────────────────────────────────────
        self._time_label = QLabel("25:00")
        self._time_label.setObjectName("timerDisplay")
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._time_label)

        # ── Inspirational quote ───────────────────────────────────────
        self._quote_text = QLabel("")
        self._quote_text.setObjectName("quoteText")
        self._quote_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._quote_text.setWordWrap(True)
        layout.addWidget(self._quote_text)

        self._quote_author = QLabel("")
        self._quote_author.setObjectName("quoteAuthor")
        self._quote_author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._quote_author)

        # ── Daily progress ────────────────────────────────────────────
        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximum(100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        layout.addWidget(self._progress_bar)

        self._progress_label = QLabel("")
        self._progress_label.setObjectName("progressLabel")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._progress_label)

        layout.addSpacing(8)

        # ── Task description ──────────────────────────────────────────
        task_row = QHBoxLayout()
        task_row.addWidget(QLabel("Current task:"))
        self._task_input = QLineEdit()
        self._task_input.setPlaceholderText("What are you working on?")
        task_row.addWidget(self._task_input, 1)
        layout.addLayout(task_row)

        # ── Duration selection ────────────────────────────────────────
        dur_row = QHBoxLayout()
        dur_row.addWidget(QLabel("Focus time:"))

        self._preset_combo = QComboBox()
        self._preset_combo.addItem("25 min", 25)
        self._preset_combo.addItem("50 min", 50)
        self._preset_combo.addItem("90 min", 90)
        self._preset_combo.addItem("120 min", 120)
        self._preset_combo.addItem("180 min", 180)
        dur_row.addWidget(self._preset_combo)

        self._custom_spin = QSpinBox()
        self._custom_spin.setRange(1, 600)
        self._custom_spin.setValue(25)
        self._custom_spin.setSuffix(" min")
        self._custom_spin.setAccelerated(True)
        self._custom_spin.setKeyboardTracking(True)
        dur_row.addWidget(self._custom_spin)

        dur_row.addStretch()
        layout.addLayout(dur_row)

        # ── Pomodoro options ──────────────────────────────────────────
        pomo_group = QGroupBox("Pomodoro Mode")
        pomo_layout = QGridLayout(pomo_group)

        self._pomo_enabled_cb = QCheckBox("Enable Pomodoro")
        pomo_layout.addWidget(self._pomo_enabled_cb, 0, 0, 1, 2)

        pomo_layout.addWidget(QLabel("Focus:"), 1, 0)
        self._pomo_focus_spin = QSpinBox()
        self._pomo_focus_spin.setRange(5, 120)
        self._pomo_focus_spin.setValue(25)
        self._pomo_focus_spin.setSuffix(" min")
        self._pomo_focus_spin.setAccelerated(True)
        pomo_layout.addWidget(self._pomo_focus_spin, 1, 1)

        pomo_layout.addWidget(QLabel("Break:"), 2, 0)
        self._pomo_break_spin = QSpinBox()
        self._pomo_break_spin.setRange(1, 60)
        self._pomo_break_spin.setValue(5)
        self._pomo_break_spin.setSuffix(" min")
        self._pomo_break_spin.setAccelerated(True)
        pomo_layout.addWidget(self._pomo_break_spin, 2, 1)

        pomo_layout.addWidget(QLabel("Cycles:"), 3, 0)
        self._pomo_cycles_spin = QSpinBox()
        self._pomo_cycles_spin.setRange(1, 20)
        self._pomo_cycles_spin.setValue(4)
        self._pomo_cycles_spin.setAccelerated(True)
        pomo_layout.addWidget(self._pomo_cycles_spin, 3, 1)
        layout.addWidget(pomo_group)

        # ── Control buttons ───────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._start_btn = QPushButton("START FOCUS")
        self._start_btn.setObjectName("primaryButton")
        self._start_btn.setMinimumWidth(240)
        btn_row.addWidget(self._start_btn)

        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setVisible(False)
        btn_row.addWidget(self._pause_btn)

        self._save_btn = QPushButton("Save")
        self._save_btn.setToolTip(
            "Save the time already focused (shown when paused) and reset the timer."
        )
        self._save_btn.setObjectName("primaryButton")
        self._save_btn.setVisible(False)
        btn_row.addWidget(self._save_btn)

        self._reset_btn = QPushButton("Reset")
        self._reset_btn.setVisible(False)
        btn_row.addWidget(self._reset_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addStretch()
        self._update_progress_display()

    # ── Signal connections ────────────────────────────────────────────

    def _connect_signals(self) -> None:
        self._start_btn.clicked.connect(self._on_start)
        self._pause_btn.clicked.connect(self._on_pause)
        self._save_btn.clicked.connect(self._on_save)
        self._reset_btn.clicked.connect(self._on_reset)
        self._preset_combo.currentIndexChanged.connect(
            lambda: self._custom_spin.setValue(self._preset_combo.currentData())
        )
        self._pomo_enabled_cb.toggled.connect(self._on_pomo_toggled)

        self._timer.tick.connect(self._on_tick)
        self._timer.state_changed.connect(self._on_state_changed)
        self._timer.finished.connect(self._on_timer_finished)
        self._timer.pomodoro_phase_changed.connect(self._on_pomodoro_phase_changed)
        self._timer.pomodoro_complete.connect(self._on_pomodoro_complete)

    # ── Slots ─────────────────────────────────────────────────────────

    def _get_duration_minutes(self) -> int:
        return self._custom_spin.value()

    def _on_start(self) -> None:
        if self._timer.state == TimerState.PAUSED:
            self._timer.resume()
            return

        minutes = self._get_duration_minutes()
        self._timer.configure_pomodoro(
            enabled=self._pomo_enabled_cb.isChecked(),
            focus_min=self._pomo_focus_spin.value(),
            break_min=self._pomo_break_spin.value(),
            cycles=self._pomo_cycles_spin.value(),
        )
        self._timer.start(minutes * 60)
        self._time_label.setText(self._timer.format_time(self._timer.remaining))

        # Disable config while running
        self._set_config_enabled(False)

    def _on_pause(self) -> None:
        if self._timer.state == TimerState.RUNNING:
            self._timer.pause()
            self._pause_btn.setText("Resume")
        else:
            self._timer.resume()
            self._pause_btn.setText("Pause")

    def _reset_to_idle(self) -> None:
        """Stop the timer and restore the configured initial duration."""
        self._timer.reset()
        minutes = self._get_duration_minutes()
        self._timer.set_duration(minutes * 60)
        self._time_label.setText(self._timer.format_time(self._timer.remaining))
        self._phase_label.setVisible(False)
        self._set_config_enabled(True)
        self._update_progress_display()

    def _on_reset(self) -> None:
        self._reset_to_idle()

    def _on_save(self) -> None:
        """Save the time already focused (elapsed) as a completed session."""
        if self._timer.state != TimerState.PAUSED:
            return

        # Only save focus time, never break time
        if self._timer.current_phase != PomodoroPhase.FOCUS:
            QMessageBox.information(
                self, "Cannot Save",
                "Break time is not counted toward your focus goal."
            )
            return

        elapsed = self._timer.elapsed
        if elapsed < 1:
            return  # nothing meaningful to save

        minutes = elapsed // 60
        seconds = elapsed % 60
        task_desc = self._task_input.text().strip()

        reply = QMessageBox.question(
            self, "Save Session",
            f"Save {minutes}m {seconds}s of focused time as a completed session?\n"
            + (f'Task: "{task_desc}"\n' if task_desc else ""),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Record the partial session (counts toward today's goal)
        self.session_completed.emit(elapsed, task_desc)
        self._reset_to_idle()

    def _on_tick(self, remaining: int, total: int) -> None:
        self._time_label.setText(FocusTimer.format_time(remaining))

    def _on_state_changed(self, state: TimerState) -> None:
        if state == TimerState.IDLE:
            self._start_btn.setText("START FOCUS")
            self._start_btn.setVisible(True)
            self._pause_btn.setVisible(False)
            self._save_btn.setVisible(False)
            self._reset_btn.setVisible(False)
            self._set_config_enabled(True)
        elif state == TimerState.RUNNING:
            self._start_btn.setVisible(False)
            self._pause_btn.setText("Pause")
            self._pause_btn.setVisible(True)
            self._save_btn.setVisible(False)
            self._reset_btn.setVisible(True)
        elif state == TimerState.PAUSED:
            self._pause_btn.setText("Resume")
            self._save_btn.setVisible(True)

    def _on_timer_finished(self) -> None:
        """A single focus (or break) period ended."""
        if self._timer.current_phase == PomodoroPhase.FOCUS or \
           not self._pomo_enabled_cb.isChecked():
            # Focus session completed
            duration = self._timer.total  # total focus seconds
            task_desc = self._task_input.text().strip()
            self.session_completed.emit(duration, task_desc)
            self._update_progress_display()
            # Refresh quote for next session
            quote_freq = self._db.get_setting("quote_frequency", "per_session")
            if quote_freq != "daily":
                self._refresh_quote()

    def _on_pomodoro_phase_changed(self, phase: PomodoroPhase, cycle: int) -> None:
        if phase == PomodoroPhase.FOCUS:
            self._phase_label.setText(f"Focus — Cycle {cycle}/{self._pomo_cycles_spin.value()}")
        else:
            self._phase_label.setText(f"Break — Cycle {cycle}/{self._pomo_cycles_spin.value()}")
        self._phase_label.setVisible(True)

    def _on_pomodoro_complete(self) -> None:
        QMessageBox.information(
            self, "Pomodoro Complete",
            f"All {self._pomo_cycles_spin.value()} Pomodoro cycles are done! "
            "Great work!"
        )
        self._phase_label.setVisible(False)
        self._set_config_enabled(True)
        self._update_progress_display()

    def _on_pomo_toggled(self, enabled: bool) -> None:
        """Enable/disable Pomodoro mode controls."""
        pass  # Configuration is read on start

    # ── Helpers ───────────────────────────────────────────────────────

    def _set_config_enabled(self, enabled: bool) -> None:
        """Enable or disable config controls during/after a session."""
        self._preset_combo.setEnabled(enabled)
        self._custom_spin.setEnabled(enabled)
        self._pomo_enabled_cb.setEnabled(enabled)
        self._pomo_focus_spin.setEnabled(enabled)
        self._pomo_break_spin.setEnabled(enabled)
        self._pomo_cycles_spin.setEnabled(enabled)
        self._task_input.setEnabled(enabled)

    def _refresh_quote(self) -> None:
        """Pick a random quote from the database and display it."""
        quotes = self._db.get_quotes(include_builtin=True)
        if quotes:
            q = random.choice(quotes)
            self._current_quote = (q["text"], q["author"])
            self._quote_text.setText(f'"{q["text"]}"')
            self._quote_author.setText(f"— {q['author']}" if q["author"] else "")
        else:
            self._quote_text.setText("")
            self._quote_author.setText("")

    def _update_progress_display(self) -> None:
        """Update the daily progress bar and label."""
        today_seconds = self._db.get_today_total_seconds()
        goal_minutes = self._db.get_today_goal_minutes()
        goal_seconds = goal_minutes * 60

        pct = min(100, int(today_seconds / goal_seconds * 100)) if goal_seconds > 0 else 0
        self._progress_bar.setValue(pct)

        today_hours = today_seconds / 3600
        goal_hours = goal_seconds / 3600
        self._progress_label.setText(
            f"Today: {today_hours:.1f} / {goal_hours:.1f} hours  ({pct}%)"
        )

    def refresh_on_navigate(self) -> None:
        """Called when user navigates to this page."""
        self._update_progress_display()
