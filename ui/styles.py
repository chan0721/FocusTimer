"""
Light and dark QSS stylesheets for the FocusTimer minimal academic UI.
"""

# ── Shared base constants ─────────────────────────────────────────────
FONT_FAMILY = '"Segoe UI", "Helvetica Neue", Arial, sans-serif'
FONT_SIZE_SM = "12px"
FONT_SIZE_MD = "14px"
FONT_SIZE_LG = "16px"
BORDER_RADIUS = "8px"
BUTTON_RADIUS = "6px"

# ── Light theme ───────────────────────────────────────────────────────

LIGHT_QSS = f"""
/* ── Global ──────────────────────────────────────────────── */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_MD};
    color: #2c3e50;
}}

QMainWindow {{
    background-color: #f8f9fa;
}}

/* ── Sidebar ─────────────────────────────────────────────── */
#sidebar {{
    background-color: #ffffff;
    border-right: 1px solid #e9ecef;
}}

#sidebar QPushButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    font-size: {FONT_SIZE_MD};
    color: #495057;
    background: transparent;
    margin: 2px 8px;
}}

#sidebar QPushButton:hover {{
    background-color: #e9ecef;
    color: #212529;
}}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {{
    background-color: #d3e3fd;
    color: #1a73e8;
    font-weight: 600;
}}

#sidebarLabel {{
    font-size: {FONT_SIZE_SM};
    color: #868e96;
    padding: 4px 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Content pages ───────────────────────────────────────── */
#pageContainer {{
    background-color: #f8f9fa;
}}

/* ── Timer page ──────────────────────────────────────────── */
#timerDisplay {{
    font-size: 72px;
    font-weight: 300;
    color: #2c3e50;
    letter-spacing: 4px;
}}

#phaseLabel {{
    font-size: {FONT_SIZE_LG};
    color: #6c757d;
    font-weight: 500;
}}

#quoteText {{
    font-size: {FONT_SIZE_LG};
    color: #495057;
    font-style: italic;
    padding: 8px 0px;
}}

#quoteAuthor {{
    font-size: {FONT_SIZE_MD};
    color: #868e96;
}}

#progressLabel {{
    font-size: {FONT_SIZE_SM};
    color: #6c757d;
}}

/* ── Buttons ─────────────────────────────────────────────── */
QPushButton {{
    background-color: #e9ecef;
    color: #495057;
    border: 1px solid #dee2e6;
    border-radius: {BUTTON_RADIUS};
    padding: 8px 18px;
    font-size: {FONT_SIZE_MD};
}}

QPushButton:hover {{
    background-color: #dee2e6;
    border-color: #ced4da;
}}

QPushButton:pressed {{
    background-color: #ced4da;
}}

#primaryButton {{
    background-color: #1a73e8;
    color: #ffffff;
    border: none;
    font-size: {FONT_SIZE_LG};
    font-weight: 600;
    padding: 14px 48px;
    border-radius: 10px;
}}

#primaryButton:hover {{
    background-color: #1557b0;
}}

#primaryButton:pressed {{
    background-color: #12479a;
}}

#dangerButton {{
    background-color: #e74c3c;
    color: #ffffff;
    border: none;
}}

#dangerButton:hover {{
    background-color: #c0392b;
}}

/* ── Input fields ────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    color: #2c3e50;
    font-size: {FONT_SIZE_MD};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: #1a73e8;
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    selection-background-color: #d3e3fd;
    selection-color: #1a73e8;
}}

QSpinBox {{
    min-width: 90px;
}}

QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #dee2e6;
    border-bottom: 1px solid #dee2e6;
    border-top-right-radius: {BORDER_RADIUS};
}}

QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border-left: 1px solid #dee2e6;
    border-bottom-right-radius: {BORDER_RADIUS};
}}

QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
}}

/* ── Table views ─────────────────────────────────────────── */
QTableWidget {{
    background-color: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: {BORDER_RADIUS};
    gridline-color: #f1f3f5;
    selection-background-color: #d3e3fd;
    selection-color: #2c3e50;
}}

QTableWidget::item {{
    padding: 8px 12px;
}}

QHeaderView::section {{
    background-color: #f8f9fa;
    border: none;
    border-bottom: 2px solid #dee2e6;
    padding: 8px 12px;
    font-weight: 600;
    color: #495057;
}}

/* ── Scroll bars ─────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #ced4da;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #adb5bd;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: #ced4da;
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #adb5bd;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Progress bar ────────────────────────────────────────── */
QProgressBar {{
    background-color: #e9ecef;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: {FONT_SIZE_SM};
    color: #495057;
}}

QProgressBar::chunk {{
    background-color: #1a73e8;
    border-radius: 6px;
}}

/* ── Group box ───────────────────────────────────────────── */
QGroupBox {{
    font-weight: 600;
    color: #495057;
    border: 1px solid #e9ecef;
    border-radius: {BORDER_RADIUS};
    margin-top: 12px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}}

/* ── Tab widget ──────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #e9ecef;
    border-radius: {BORDER_RADIUS};
    background-color: #ffffff;
}}

QTabBar::tab {{
    background-color: #f1f3f5;
    border: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #6c757d;
}}

QTabBar::tab:selected {{
    background-color: #ffffff;
    color: #1a73e8;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: #e9ecef;
}}

/* ── Slider ──────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: #e9ecef;
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #1a73e8;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background: #1a73e8;
    border-radius: 3px;
}}

/* ── Checkbox / Radio ────────────────────────────────────── */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: #2c3e50;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #ced4da;
    border-radius: 4px;
    background-color: #ffffff;
}}

QCheckBox::indicator:checked {{
    background-color: #1a73e8;
    border-color: #1a73e8;
}}

QRadioButton::indicator {{
    border-radius: 10px;
}}

QRadioButton::indicator:checked {{
    background-color: #1a73e8;
    border-color: #1a73e8;
}}

/* ── Splitter ────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: #e9ecef;
    width: 1px;
}}

/* ── Tooltip ─────────────────────────────────────────────── */
QToolTip {{
    background-color: #2c3e50;
    color: #ffffff;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: {FONT_SIZE_SM};
}}
"""

# ── Dark theme ─────────────────────────────────────────────────────────

DARK_QSS = f"""
/* ── Global ──────────────────────────────────────────────── */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_MD};
    color: #e1e4e8;
}}

QMainWindow {{
    background-color: #1a1d23;
}}

/* ── Sidebar ─────────────────────────────────────────────── */
#sidebar {{
    background-color: #21252b;
    border-right: 1px solid #2d3139;
}}

#sidebar QPushButton {{
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    font-size: {FONT_SIZE_MD};
    color: #8b949e;
    background: transparent;
    margin: 2px 8px;
}}

#sidebar QPushButton:hover {{
    background-color: #2d3139;
    color: #c9d1d9;
}}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {{
    background-color: #1f3a5f;
    color: #58a6ff;
    font-weight: 600;
}}

#sidebarLabel {{
    font-size: {FONT_SIZE_SM};
    color: #484f58;
    padding: 4px 16px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Content pages ───────────────────────────────────────── */
#pageContainer {{
    background-color: #1a1d23;
}}

/* ── Timer page ──────────────────────────────────────────── */
#timerDisplay {{
    font-size: 72px;
    font-weight: 300;
    color: #e1e4e8;
    letter-spacing: 4px;
}}

#phaseLabel {{
    font-size: {FONT_SIZE_LG};
    color: #8b949e;
    font-weight: 500;
}}

#quoteText {{
    font-size: {FONT_SIZE_LG};
    color: #c9d1d9;
    font-style: italic;
    padding: 8px 0px;
}}

#quoteAuthor {{
    font-size: {FONT_SIZE_MD};
    color: #6e7681;
}}

#progressLabel {{
    font-size: {FONT_SIZE_SM};
    color: #8b949e;
}}

/* ── Buttons ─────────────────────────────────────────────── */
QPushButton {{
    background-color: #2d3139;
    color: #c9d1d9;
    border: 1px solid #373c44;
    border-radius: {BUTTON_RADIUS};
    padding: 8px 18px;
    font-size: {FONT_SIZE_MD};
}}

QPushButton:hover {{
    background-color: #373c44;
    border-color: #484f58;
}}

QPushButton:pressed {{
    background-color: #444c56;
}}

#primaryButton {{
    background-color: #1f6feb;
    color: #ffffff;
    border: none;
    font-size: {FONT_SIZE_LG};
    font-weight: 600;
    padding: 14px 48px;
    border-radius: 10px;
}}

#primaryButton:hover {{
    background-color: #388bfd;
}}

#primaryButton:pressed {{
    background-color: #1f6feb;
}}

#dangerButton {{
    background-color: #da3633;
    color: #ffffff;
    border: none;
}}

#dangerButton:hover {{
    background-color: #f85149;
}}

/* ── Input fields ────────────────────────────────────────── */
QLineEdit, QSpinBox, QComboBox {{
    background-color: #21252b;
    border: 1px solid #373c44;
    border-radius: {BORDER_RADIUS};
    padding: 8px 12px;
    color: #e1e4e8;
    font-size: {FONT_SIZE_MD};
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: #58a6ff;
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: #21252b;
    border: 1px solid #373c44;
    selection-background-color: #1f3a5f;
    selection-color: #58a6ff;
}}

QSpinBox {{
    min-width: 90px;
}}

QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 22px;
    border-left: 1px solid #373c44;
    border-bottom: 1px solid #373c44;
    border-top-right-radius: {BORDER_RADIUS};
}}

QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 22px;
    border-left: 1px solid #373c44;
    border-bottom-right-radius: {BORDER_RADIUS};
}}

QSpinBox::up-arrow, QSpinBox::down-arrow {{
    width: 8px;
    height: 8px;
}}

/* ── Table views ─────────────────────────────────────────── */
QTableWidget {{
    background-color: #21252b;
    border: 1px solid #2d3139;
    border-radius: {BORDER_RADIUS};
    gridline-color: #2d3139;
    selection-background-color: #1f3a5f;
    selection-color: #e1e4e8;
}}

QTableWidget::item {{
    padding: 8px 12px;
}}

QHeaderView::section {{
    background-color: #1a1d23;
    border: none;
    border-bottom: 2px solid #373c44;
    padding: 8px 12px;
    font-weight: 600;
    color: #8b949e;
}}

/* ── Scroll bars ─────────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: #484f58;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #6e7681;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background: #484f58;
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: #6e7681;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* ── Progress bar ────────────────────────────────────────── */
QProgressBar {{
    background-color: #2d3139;
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: {FONT_SIZE_SM};
    color: #8b949e;
}}

QProgressBar::chunk {{
    background-color: #1f6feb;
    border-radius: 6px;
}}

/* ── Group box ───────────────────────────────────────────── */
QGroupBox {{
    font-weight: 600;
    color: #c9d1d9;
    border: 1px solid #2d3139;
    border-radius: {BORDER_RADIUS};
    margin-top: 12px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: #8b949e;
}}

/* ── Tab widget ──────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid #2d3139;
    border-radius: {BORDER_RADIUS};
    background-color: #21252b;
}}

QTabBar::tab {{
    background-color: #1a1d23;
    border: none;
    padding: 8px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    color: #8b949e;
}}

QTabBar::tab:selected {{
    background-color: #21252b;
    color: #58a6ff;
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: #2d3139;
}}

/* ── Slider ──────────────────────────────────────────────── */
QSlider::groove:horizontal {{
    background: #2d3139;
    height: 6px;
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #58a6ff;
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}

QSlider::sub-page:horizontal {{
    background: #58a6ff;
    border-radius: 3px;
}}

/* ── Checkbox / Radio ────────────────────────────────────── */
QCheckBox, QRadioButton {{
    spacing: 8px;
    color: #e1e4e8;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid #484f58;
    border-radius: 4px;
    background-color: #2d3139;
}}

QCheckBox::indicator:checked {{
    background-color: #1f6feb;
    border-color: #1f6feb;
}}

QRadioButton::indicator {{
    border-radius: 10px;
}}

QRadioButton::indicator:checked {{
    background-color: #1f6feb;
    border-color: #1f6feb;
}}

/* ── Splitter ────────────────────────────────────────────── */
QSplitter::handle {{
    background-color: #2d3139;
    width: 1px;
}}

/* ── Tooltip ─────────────────────────────────────────────── */
QToolTip {{
    background-color: #484f58;
    color: #e1e4e8;
    border: none;
    border-radius: 4px;
    padding: 6px 10px;
    font-size: {FONT_SIZE_SM};
}}
"""


def get_stylesheet(theme: str) -> str:
    """Return the full QSS stylesheet for the given theme name."""
    if theme == "dark":
        return DARK_QSS
    return LIGHT_QSS
