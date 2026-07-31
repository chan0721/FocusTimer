"""
FocusTimer — Entry Point
A Windows desktop focus timer with Pomodoro, statistics, quotes, and ambient sounds.

Usage:
    python main.py
"""

import sys
import os

# Ensure the project root is on sys.path so imports work when running directly
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Initialize pygame early (before any Qt windows).
# Full init is needed so pygame.event.get() works for music-end events.
import pygame
pygame.init()

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow


def main() -> None:
    # High-DPI scaling support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("FocusTimer")
    app.setOrganizationName("FocusTimer")

    window = MainWindow(app)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
