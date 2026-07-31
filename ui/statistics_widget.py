"""
Statistics page with daily/weekly/monthly charts and a GitHub-style calendar heatmap.
Embeds matplotlib figures inside the PyQt6 widget.
"""

from datetime import date, timedelta
import calendar

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout, QComboBox,
)
from PyQt6.QtCore import Qt

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.patches as mpatches
import numpy as np

from database.database import Database


class StatisticsWidget(QWidget):
    """Statistics dashboard view."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Statistics")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        self._period_combo = QComboBox()
        self._period_combo.addItem("Last 7 Days", 7)
        self._period_combo.addItem("Last 30 Days", 30)
        self._period_combo.addItem("Last 90 Days", 90)
        self._period_combo.currentIndexChanged.connect(self._on_period_changed)
        header.addWidget(self._period_combo)
        layout.addLayout(header)

        # ── Today summary cards ───────────────────────────────────────
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self._today_time_card = self._make_summary_card("Today's Focus", "0h 0m")
        cards_layout.addWidget(self._today_time_card)

        self._today_sessions_card = self._make_summary_card("Sessions", "0")
        cards_layout.addWidget(self._today_sessions_card)

        self._goal_card = self._make_summary_card("Goal Progress", "0%")
        cards_layout.addWidget(self._goal_card)

        self._weekly_avg_card = self._make_summary_card("Weekly Avg", "0h 0m")
        cards_layout.addWidget(self._weekly_avg_card)

        layout.addLayout(cards_layout)

        # ── Bar chart ─────────────────────────────────────────────────
        self._bar_figure = Figure(figsize=(8, 3), dpi=100)
        self._bar_figure.set_tight_layout(True)
        self._bar_canvas = FigureCanvasQTAgg(self._bar_figure)
        layout.addWidget(self._bar_canvas)

        # ── Calendar heatmap ──────────────────────────────────────────
        heatmap_group = QGroupBox("Focus Calendar Heatmap")
        heatmap_layout = QVBoxLayout(heatmap_group)
        self._heatmap_figure = Figure(figsize=(10, 2.5), dpi=100)
        self._heatmap_figure.set_tight_layout(True)
        self._heatmap_canvas = FigureCanvasQTAgg(self._heatmap_figure)
        heatmap_layout.addWidget(self._heatmap_canvas)
        layout.addWidget(heatmap_group)

        layout.addStretch()

    def _make_summary_card(self, label: str, value: str) -> QGroupBox:
        """Create a small card with a label and large value."""
        gb = QGroupBox()
        gb.setStyleSheet(
            "QGroupBox { border: 1px solid #e9ecef; border-radius: 8px; padding: 12px; }"
            "QGroupBox::title { color: #6c757d; }"
        )
        inner = QVBoxLayout(gb)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet("font-size: 24px; font-weight: 700; color: #2c3e50;")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(val_lbl)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #868e96;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(lbl)
        return gb

    # ── Public refresh ────────────────────────────────────────────────

    def refresh_on_navigate(self) -> None:
        """Called every time the user navigates to this page."""
        self._refresh_all()

    def _on_period_changed(self) -> None:
        self._refresh_all()

    def _refresh_all(self) -> None:
        today = date.today()
        days = self._period_combo.currentData()
        start = today - timedelta(days=days - 1)

        # Fetch data
        daily_totals = self._db.get_daily_totals(start, today)
        today_seconds = self._db.get_today_total_seconds()
        today_sessions = self._db.get_today_session_count()
        goal_minutes = self._db.get_today_goal_minutes()

        # ── Update cards ──────────────────────────────────────────────
        h = today_seconds // 3600
        m = (today_seconds % 3600) // 60
        self._today_time_card.findChild(QLabel).setText(f"{h}h {m}m")
        self._today_sessions_card.findChild(QLabel).setText(str(today_sessions))
        pct = min(100, int(today_seconds / (goal_minutes * 60) * 100)) if goal_minutes > 0 else 0
        self._goal_card.findChild(QLabel).setText(f"{pct}%")

        # Weekly average
        week_start = today - timedelta(days=6)
        week_totals = [daily_totals.get((week_start + timedelta(days=i)).isoformat(), 0)
                       for i in range(7)]
        week_avg = sum(week_totals) / 7 if week_totals else 0
        avg_h = int(week_avg // 3600)
        avg_m = int((week_avg % 3600) // 60)
        self._weekly_avg_card.findChild(QLabel).setText(f"{avg_h}h {avg_m}m")

        # ── Bar chart ─────────────────────────────────────────────────
        self._draw_bar_chart(daily_totals, start, today)

        # ── Calendar heatmap (always last ~4 months) ──────────────────
        self._draw_heatmap()

    def _draw_bar_chart(self, daily_totals: dict[str, int], start: date, end: date) -> None:
        self._bar_figure.clear()
        ax = self._bar_figure.add_subplot(111)

        dates_list = [start + timedelta(days=i) for i in range((end - start).days + 1)]
        values = [daily_totals.get(d.isoformat(), 0) / 3600 for d in dates_list]
        labels = [d.strftime("%a\n%m/%d") for d in dates_list]

        colors = ["#1a73e8" if d == date.today() else "#a8c7fa" for d in dates_list]
        bars = ax.bar(range(len(dates_list)), values, color=colors, edgecolor="white", linewidth=0.5)

        if len(dates_list) <= 14:
            ax.set_xticks(range(len(dates_list)))
            ax.set_xticklabels(labels, fontsize=8)
        else:
            # Show fewer labels for longer ranges
            step = max(1, len(dates_list) // 10)
            ax.set_xticks(range(0, len(dates_list), step))
            ax.set_xticklabels([labels[i] for i in range(0, len(dates_list), step)], fontsize=8)

        ax.set_ylabel("Hours", fontsize=10)
        ax.set_title("Daily Focus Time", fontsize=12, fontweight="bold", color="#2c3e50")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(labelsize=8)
        ax.yaxis.grid(True, linestyle="--", alpha=0.3)

        self._bar_canvas.draw()

    def _draw_heatmap(self) -> None:
        """GitHub-style calendar heatmap for the last ~4 months."""
        self._heatmap_figure.clear()
        ax = self._heatmap_figure.add_subplot(111)

        today = date.today()
        # Show ~17 weeks back (~4 months)
        start = today - timedelta(days=119)  # 17 weeks
        # Align to Monday
        start = start - timedelta(days=start.weekday())

        # Get data
        daily_totals = self._db.get_daily_totals(start, today)

        num_weeks = (today - start).days // 7 + 1
        data = np.zeros((7, num_weeks))

        for week_idx in range(num_weeks):
            for day_idx in range(7):
                d = start + timedelta(days=week_idx * 7 + day_idx)
                if d > today:
                    data[day_idx, week_idx] = np.nan
                else:
                    seconds = daily_totals.get(d.isoformat(), 0)
                    data[day_idx, week_idx] = seconds / 3600.0  # hours

        # Color mapping: 0 = gray, max = deep blue
        max_val = np.nanmax(data) if not np.all(np.isnan(data)) else 1
        if max_val == 0:
            max_val = 1

        cmap_colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
        bounds = [0, 0.25 * max_val, 0.5 * max_val, 0.75 * max_val, max_val]

        for week_idx in range(num_weeks):
            for day_idx in range(7):
                val = data[day_idx, week_idx]
                if np.isnan(val):
                    continue
                color = cmap_colors[0]
                for b_idx, b_val in enumerate(bounds):
                    if val > b_val:
                        color = cmap_colors[min(b_idx + 1, len(cmap_colors) - 1)]
                rect = mpatches.Rectangle(
                    (week_idx, 6 - day_idx), 1, 1,
                    linewidth=2, edgecolor="white", facecolor=color,
                )
                ax.add_patch(rect)

        ax.set_xlim(0, num_weeks)
        ax.set_ylim(0, 7)
        ax.set_aspect("equal")
        ax.axis("off")

        # Month labels
        month_starts = {}
        for week_idx in range(num_weeks):
            d = start + timedelta(days=week_idx * 7)
            key = d.strftime("%b")
            if key not in month_starts:
                month_starts[key] = week_idx
        for month, pos in month_starts.items():
            ax.text(pos + 0.5, 7.3, month, ha="center", fontsize=9, color="#6c757d")

        # Day labels (left side)
        day_names = ["Mon", "", "Wed", "", "Fri", "", ""]
        for i, name in enumerate(day_names):
            if name:
                ax.text(-0.8, 6 - i + 0.5, name, ha="right", va="center",
                        fontsize=8, color="#6c757d")

        self._heatmap_canvas.draw()
