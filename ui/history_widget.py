"""
History page — tabular view of past focus sessions with search and filtering.
"""

from datetime import date, datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QDateEdit, QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt, QDate

from database.database import Database


class HistoryWidget(QWidget):
    """History view showing all past focus sessions."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._init_ui()
        self.refresh_on_navigate()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Session History")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        # Date range filter
        header.addWidget(QLabel("From:"))
        self._from_date = QDateEdit()
        self._from_date.setCalendarPopup(True)
        self._from_date.setDate(QDate.currentDate().addMonths(-1))
        header.addWidget(self._from_date)

        header.addWidget(QLabel("To:"))
        self._to_date = QDateEdit()
        self._to_date.setCalendarPopup(True)
        self._to_date.setDate(QDate.currentDate())
        header.addWidget(self._to_date)

        self._filter_btn = QPushButton("Filter")
        self._filter_btn.clicked.connect(self._load_data)
        header.addWidget(self._filter_btn)

        layout.addLayout(header)

        # ── Search bar ────────────────────────────────────────────────
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter by task description...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_row.addWidget(self._search_input, 1)
        layout.addLayout(search_row)

        # ── Summary label ─────────────────────────────────────────────
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #6c757d; font-size: 13px;")
        layout.addWidget(self._summary_label)

        # ── Table ─────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Date", "Start Time", "Duration", "Task", "Status"]
        )
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)

        # ── Action buttons ────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._delete_btn = QPushButton("Delete Selected")
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.clicked.connect(self._delete_selected)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _on_search_changed(self) -> None:
        self._load_data()

    def _load_data(self) -> None:
        """Query the database and populate the table."""
        from_d = self._from_date.date().toPyDate()
        to_d = self._to_date.date().toPyDate()
        search = self._search_input.text().strip()

        sessions = self._db.get_sessions(
            start_date=from_d,
            end_date=to_d,
            search_text=search,
        )

        self._table.setRowCount(len(sessions))
        total_seconds = 0

        for row_idx, sess in enumerate(sessions):
            # Date
            self._table.setItem(row_idx, 0, QTableWidgetItem(sess["session_date"]))
            # Start time
            self._table.setItem(row_idx, 1, QTableWidgetItem(sess["start_time"]))
            # Duration
            dur = sess["duration"]
            total_seconds += dur if sess["completed"] else 0
            h = dur // 3600
            m = (dur % 3600) // 60
            s = dur % 60
            dur_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
            self._table.setItem(row_idx, 2, QTableWidgetItem(dur_str))
            # Task
            self._table.setItem(row_idx, 3, QTableWidgetItem(sess["task_desc"]))
            # Status
            status = "✓ Completed" if sess["completed"] else "✗ Abandoned"
            st_item = QTableWidgetItem(status)
            if not sess["completed"]:
                st_item.setForeground(Qt.GlobalColor.red)
            self._table.setItem(row_idx, 4, st_item)

            # Store row id as hidden data in column 0
            self._table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, sess["id"])

        # Summary
        h_total = total_seconds // 3600
        m_total = (total_seconds % 3600) // 60
        self._summary_label.setText(
            f"{len(sessions)} sessions  ·  Total focused: {h_total}h {m_total}m"
        )

    def _delete_selected(self) -> None:
        rows = set()
        for item in self._table.selectedItems():
            rows.add(item.row())

        if not rows:
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(rows)} selected session(s)? This cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for row in sorted(rows, reverse=True):
            session_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if session_id:
                self._db.delete_session(session_id)
            self._table.removeRow(row)

        self._load_data()

    def refresh_on_navigate(self) -> None:
        self._load_data()
