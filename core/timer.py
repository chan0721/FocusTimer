"""
Focus countdown timer with Pomodoro cycle support.
Emits Qt signals so the UI can react to state changes.
"""

import enum
from datetime import datetime

from PyQt6.QtCore import QTimer, QObject, pyqtSignal


class TimerState(enum.Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


class PomodoroPhase(enum.Enum):
    FOCUS = "focus"
    BREAK = "break"


class FocusTimer(QObject):
    """Manages countdown state, Pomodoro cycles, and emits progress signals."""

    # Emitted every second with (remaining_seconds, total_seconds)
    tick = pyqtSignal(int, int)
    # Emitted when the timer reaches zero
    finished = pyqtSignal()
    # Emitted when state changes
    state_changed = pyqtSignal(TimerState)
    # Pomodoro phase changed (new phase, cycle_number)
    pomodoro_phase_changed = pyqtSignal(PomodoroPhase, int)
    # All pomodoro cycles complete
    pomodoro_complete = pyqtSignal()

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent)
        self._qtimer = QTimer(self)
        self._qtimer.timeout.connect(self._on_tick)
        self._qtimer.setInterval(1000)  # fire every second

        self._state = TimerState.IDLE
        self._remaining = 0       # seconds
        self._total = 0           # seconds (initial duration)
        self._start_datetime: datetime | None = None

        # Pomodoro settings
        self._pomodoro_enabled = False
        self._focus_seconds = 25 * 60
        self._break_seconds = 5 * 60
        self._total_cycles = 4
        self._current_cycle = 0
        self._current_phase = PomodoroPhase.FOCUS

    # ── Properties ────────────────────────────────────────────────────

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def remaining(self) -> int:
        return self._remaining

    @property
    def total(self) -> int:
        return self._total

    @property
    def elapsed(self) -> int:
        """Seconds elapsed since start (accounting for pauses)."""
        return self._total - self._remaining

    @property
    def is_running(self) -> bool:
        return self._state == TimerState.RUNNING

    @property
    def start_datetime(self) -> datetime | None:
        return self._start_datetime

    @property
    def current_phase(self) -> PomodoroPhase:
        return self._current_phase

    @property
    def current_cycle(self) -> int:
        return self._current_cycle

    # ── Configuration ─────────────────────────────────────────────────

    def set_duration(self, total_seconds: int) -> None:
        """Set the countdown duration. Only effective when IDLE."""
        if self._state != TimerState.IDLE:
            return
        self._total = total_seconds
        self._remaining = total_seconds

    def configure_pomodoro(
        self,
        enabled: bool,
        focus_min: int = 25,
        break_min: int = 5,
        cycles: int = 4,
    ) -> None:
        self._pomodoro_enabled = enabled
        self._focus_seconds = focus_min * 60
        self._break_seconds = break_min * 60
        self._total_cycles = cycles

    # ── Controls ──────────────────────────────────────────────────────

    def start(self, duration_seconds: int | None = None) -> None:
        """Begin countdown. If already paused, resume instead."""
        if self._state == TimerState.PAUSED:
            self.resume()
            return

        if duration_seconds is not None:
            self.set_duration(duration_seconds)
        if self._total <= 0:
            return

        if self._pomodoro_enabled:
            self._current_cycle = 1
            self._current_phase = PomodoroPhase.FOCUS
            self._remaining = self._focus_seconds
            self._total = self._focus_seconds
            self.pomodoro_phase_changed.emit(self._current_phase, self._current_cycle)

        self._remaining = self._total if self._remaining == 0 else self._remaining
        self._start_datetime = datetime.now()
        self._state = TimerState.RUNNING
        self._qtimer.start()
        self.state_changed.emit(self._state)

    def pause(self) -> None:
        if self._state != TimerState.RUNNING:
            return
        self._state = TimerState.PAUSED
        self._qtimer.stop()
        self.state_changed.emit(self._state)

    def resume(self) -> None:
        if self._state != TimerState.PAUSED:
            return
        self._state = TimerState.RUNNING
        self._qtimer.start()
        self.state_changed.emit(self._state)

    def reset(self) -> None:
        """Stop and reset to initial duration."""
        self._qtimer.stop()
        self._state = TimerState.IDLE
        self._remaining = self._total
        self._start_datetime = None
        self._current_cycle = 0
        self._current_phase = PomodoroPhase.FOCUS
        self.state_changed.emit(self._state)

    # ── Internal tick ─────────────────────────────────────────────────

    def _on_tick(self) -> None:
        if self._remaining <= 0:
            self._qtimer.stop()
            self._handle_completion()
            return

        self._remaining -= 1
        self.tick.emit(self._remaining, self._total)

    def _handle_completion(self) -> None:
        """Called when the countdown reaches zero."""
        if self._pomodoro_enabled:
            if self._current_phase == PomodoroPhase.FOCUS:
                # Focus just ended → emit finished BEFORE phase change
                self.finished.emit()
                self._current_phase = PomodoroPhase.BREAK
                self._remaining = self._break_seconds
                self._total = self._break_seconds
                self.pomodoro_phase_changed.emit(self._current_phase, self._current_cycle)
                self._state = TimerState.RUNNING
                self._qtimer.start()
            else:
                # Break just ended
                if self._current_cycle >= self._total_cycles:
                    # All cycles complete
                    self._state = TimerState.IDLE
                    self._current_cycle = 0
                    self._current_phase = PomodoroPhase.FOCUS
                    self._qtimer.stop()
                    self.state_changed.emit(self._state)
                    self.pomodoro_complete.emit()
                else:
                    # Start next focus cycle
                    self._current_cycle += 1
                    self._current_phase = PomodoroPhase.FOCUS
                    self._remaining = self._focus_seconds
                    self._total = self._focus_seconds
                    self.pomodoro_phase_changed.emit(self._current_phase, self._current_cycle)
                    self.finished.emit()
                    self._state = TimerState.RUNNING
                    self._qtimer.start()
        else:
            # Non-Pomodoro — just stop
            self._state = TimerState.IDLE
            self._qtimer.stop()
            self.state_changed.emit(self._state)
            self.finished.emit()

    # ── Formatting ────────────────────────────────────────────────────

    @staticmethod
    def format_time(total_seconds: int) -> str:
        """Convert seconds to HH:MM:SS or MM:SS string."""
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
