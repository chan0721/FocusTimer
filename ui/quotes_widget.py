"""
Quotes management page — view, add, edit, and delete inspirational quotes.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem,
    QDialog, QDialogButtonBox, QFormLayout,
    QHeaderView, QMessageBox,
)
from PyQt6.QtCore import Qt

from database.database import Database


class QuoteDialog(QDialog):
    """Modal dialog for adding or editing a quote."""

    def __init__(self, title: str, text: str = "", author: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        layout = QFormLayout(self)

        self._text_edit = QTextEdit()
        self._text_edit.setPlainText(text)
        self._text_edit.setPlaceholderText("Enter quote text...")
        self._text_edit.setMaximumHeight(100)
        layout.addRow("Quote:", self._text_edit)

        self._author_edit = QLineEdit()
        self._author_edit.setText(author)
        self._author_edit.setPlaceholderText("Author name (optional)")
        layout.addRow("Author:", self._author_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_quote(self) -> tuple[str, str]:
        return self._text_edit.toPlainText().strip(), self._author_edit.text().strip()


class QuotesWidget(QWidget):
    """View and manage inspirational quotes."""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self._db = db
        self._init_ui()
        self._load_quotes()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(12)

        # ── Header ────────────────────────────────────────────────────
        header = QHBoxLayout()
        title = QLabel("Quotes")
        title.setStyleSheet("font-size: 22px; font-weight: 600;")
        header.addWidget(title)
        header.addStretch()

        self._add_btn = QPushButton("+ Add Quote")
        self._add_btn.clicked.connect(self._add_quote)
        header.addWidget(self._add_btn)
        layout.addLayout(header)

        # ── Table ─────────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Quote", "Author", "Source"])
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setColumnWidth(1, 150)
        self._table.setColumnWidth(2, 80)
        layout.addWidget(self._table)

        # ── Actions ───────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.clicked.connect(self._edit_quote)
        btn_row.addWidget(self._edit_btn)

        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setObjectName("dangerButton")
        self._delete_btn.clicked.connect(self._delete_quote)
        btn_row.addWidget(self._delete_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _load_quotes(self) -> None:
        quotes = self._db.get_quotes(include_builtin=True)
        self._table.setRowCount(len(quotes))

        for row, q in enumerate(quotes):
            # Truncate long quotes in the table
            text = q["text"]
            display_text = text[:80] + "..." if len(text) > 80 else text
            item = QTableWidgetItem(display_text)
            item.setToolTip(text)
            self._table.setItem(row, 0, item)
            self._table.setItem(row, 1, QTableWidgetItem(q["author"]))
            source = "Built-in" if q["is_builtin"] else "User"
            src_item = QTableWidgetItem(source)
            if q["is_builtin"]:
                src_item.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(row, 2, src_item)
            # Store id
            item.setData(Qt.ItemDataRole.UserRole, q["id"])
            # Store whether builtin
            item.setData(Qt.ItemDataRole.UserRole + 1, q["is_builtin"])

    def _add_quote(self) -> None:
        dlg = QuoteDialog("Add Quote", parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            text, author = dlg.get_quote()
            if text:
                self._db.add_quote(text, author)
                self._load_quotes()

    def _edit_quote(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            return
        item = self._table.item(row, 0)
        is_builtin = item.data(Qt.ItemDataRole.UserRole + 1)
        if is_builtin:
            QMessageBox.information(
                self, "Cannot Edit",
                "Built-in quotes cannot be edited. You can add your own custom quotes."
            )
            return

        quote_id = item.data(Qt.ItemDataRole.UserRole)
        current_text = item.toolTip() or item.text()
        current_author = self._table.item(row, 1).text()

        dlg = QuoteDialog("Edit Quote", current_text, current_author, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            text, author = dlg.get_quote()
            if text:
                self._db.update_quote(quote_id, text, author)
                self._load_quotes()

    def _delete_quote(self) -> None:
        rows = set()
        for item in self._table.selectedItems():
            rows.add(item.row())

        if not rows:
            return

        # Filter out built-in quotes
        deletable = []
        for row in rows:
            item = self._table.item(row, 0)
            if item and not item.data(Qt.ItemDataRole.UserRole + 1):
                deletable.append(row)

        if not deletable:
            QMessageBox.information(
                self, "Cannot Delete",
                "Built-in quotes cannot be deleted."
            )
            return

        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete {len(deletable)} quote(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        for row in sorted(deletable, reverse=True):
            quote_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if quote_id:
                self._db.delete_quote(quote_id)

        self._load_quotes()

    def refresh_on_navigate(self) -> None:
        self._load_quotes()
