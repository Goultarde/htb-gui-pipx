"""
HTB Client Styles - Tema moderno, fluido y profesional.
Inspirado en HackTheBox: oscuro, verde neón, limpio.
"""

# HTB Green
HTB_GREEN = "#9fef00"
HTB_GREEN_DARK = "#7bc200"
HTB_GREEN_GLOW = "rgba(159, 239, 0, 0.15)"
HTB_GREEN_BORDER = "rgba(159, 239, 0, 0.25)"

# Botón principal (azul oscuro)
HTB_BTN = "#012456"
HTB_BTN_HOVER = "#023568"
HTB_BTN_PRESSED = "#011a3d"

# Background
HTB_BG_DARK = "#0a0f16"
HTB_BG_MAIN = "#101927"
HTB_BG_CARD = "#151f2e"
HTB_BG_CARD_ELEVATED = "#1a2435"
HTB_BG_HOVER = "#1a2638"
HTB_BG_INPUT = "#0d1420"
HTB_BG_INPUT_DARK = "#080c12"  # Input flag (más oscuro)

# Text
HTB_TEXT = "#e2e8f0"
HTB_TEXT_DIM = "#94a3b8"
HTB_TEXT_MUTED = "#64748b"

# Accents
ACCENT_CYAN = "#00d4ff"
ACCENT_PURPLE = "#9f7aea"
ACCENT_ORANGE = "#f6ad55"
ACCENT_RED = "#fc4747"

# Status
STATUS_SUCCESS = "#9fef00"
STATUS_WARNING = "#f6ad55"
STATUS_ERROR = "#fc4747"
STATUS_INFO = "#00d4ff"

# Difficulty
DIFF_EASY = "#9fef00"
DIFF_MEDIUM = "#f6ad55"
DIFF_HARD = "#fc4747"
DIFF_INSANE = "#9f7aea"

# NO BORDERS
HTB_BORDER = "transparent"

# ============ BUTTON STYLES (for inline use) ============
BTN_PRIMARY = f"""
    QPushButton {{
        background-color: {HTB_GREEN};
        color: #0a0f16;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 13px;
        padding: 12px 20px;
    }}
    QPushButton:hover {{
        background-color: #b0ff33;
    }}
    QPushButton:pressed {{
        background-color: {HTB_GREEN_DARK};
    }}
"""

BTN_DANGER = f"""
    QPushButton {{
        background-color: {ACCENT_RED};
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 700;
        font-size: 13px;
        padding: 12px 20px;
    }}
    QPushButton:hover {{
        background-color: #ff6060;
    }}
    QPushButton:pressed {{
        background-color: #cc3030;
    }}
"""

BTN_DEFAULT = f"""
    QPushButton {{
        background-color: {HTB_BTN};
        color: white;
        border: none;
        border-radius: 10px;
        font-weight: 600;
        font-size: 13px;
        padding: 12px 20px;
    }}
    QPushButton:hover {{
        background-color: {HTB_BTN_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {HTB_BTN_PRESSED};
    }}
"""

GLOBAL_STYLE = f"""
* {{
    font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}}

QMainWindow {{
    background-color: {HTB_BG_MAIN};
}}

QWidget {{
    color: {HTB_TEXT};
    background-color: transparent;
    border: none;
}}

/* Cards con borde sutil */
QFrame[class="card"] {{
    background-color: {HTB_BG_CARD};
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.04);
}}

/* Scrollbars */
QScrollArea {{
    background: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    border: none;
}}

QScrollBar::handle:vertical {{
    background: {HTB_TEXT_MUTED};
    min-height: 30px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background: {HTB_TEXT_DIM};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    height: 0;
    background: transparent;
    border: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    border: none;
}}

QScrollBar::handle:horizontal {{
    background: {HTB_TEXT_MUTED};
    min-width: 30px;
    border-radius: 3px;
}}

/* Labels - no border */
QLabel {{
    background: transparent;
    border: none;
}}

/* Buttons - colores sólidos, limpios */
QPushButton {{
    background-color: {HTB_BTN};
    border: none;
    border-radius: 10px;
    color: white;
    font-weight: 600;
    font-size: 13px;
    min-height: 22px;
    padding: 12px 20px;
}}

QPushButton:hover {{
    background-color: {HTB_BTN_HOVER};
}}

QPushButton:pressed {{
    background-color: {HTB_BTN_PRESSED};
}}

QPushButton:disabled {{
    color: {HTB_TEXT_MUTED};
    background-color: {HTB_BG_CARD};
}}

/* Primary Button - Verde sólido */
QPushButton[class="primary"] {{
    background-color: {HTB_GREEN};
    border: none;
    color: #0a0f16;
    font-weight: 700;
}}

QPushButton[class="primary"]:hover {{
    background-color: #b0ff33;
}}

QPushButton[class="primary"]:pressed {{
    background-color: {HTB_GREEN_DARK};
}}

/* Danger Button - Rojo sólido */
QPushButton[class="danger"] {{
    background-color: {ACCENT_RED};
    border: none;
    color: white;
    font-weight: 700;
}}

QPushButton[class="danger"]:hover {{
    background-color: #ff6060;
}}

QPushButton[class="danger"]:pressed {{
    background-color: #cc3030;
}}

/* Secondary Button - Outline verde */
QPushButton[class="secondary"] {{
    background-color: transparent;
    border: 2px solid {HTB_GREEN};
    color: {HTB_GREEN};
    font-weight: 600;
}}

QPushButton[class="secondary"]:hover {{
    background-color: {HTB_GREEN_GLOW};
}}

QPushButton[class="secondary"]:pressed {{
    background-color: rgba(159, 239, 0, 0.2);
}}

/* Line edits - limpios */
QLineEdit {{
    background-color: {HTB_BG_INPUT};
    border: none;
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    color: {HTB_TEXT};
    selection-background-color: {HTB_GREEN};
    selection-color: {HTB_BG_DARK};
}}

QLineEdit:focus {{
    background-color: {HTB_BG_CARD};
    border: 1px solid {HTB_GREEN};
}}

QLineEdit::placeholder {{
    color: {HTB_TEXT_MUTED};
}}

/* Flag input - limpio con borde verde visible */
QLineEdit#flag_input {{
    background-color: {HTB_BG_INPUT_DARK};
    border: 2px solid rgba(159, 239, 0, 0.3);
    border-radius: 10px;
    padding: 12px 16px;
    font-size: 14px;
    color: {HTB_TEXT};
    min-height: 24px;
}}

QLineEdit#flag_input:focus {{
    background-color: {HTB_BG_INPUT};
    border: 2px solid {HTB_GREEN};
}}

QLineEdit#flag_input::placeholder {{
    color: {HTB_TEXT_MUTED};
}}

/* Combo box - limpio */
QComboBox {{
    background-color: {HTB_BG_CARD};
    border: none;
    border-radius: 10px;
    padding: 10px 16px;
    font-size: 13px;
    color: {HTB_TEXT};
}}

QComboBox:hover {{
    background-color: {HTB_BG_HOVER};
}}

QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    border: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {HTB_TEXT_DIM};
}}

QComboBox QAbstractItemView {{
    background-color: {HTB_BG_CARD};
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px;
    selection-background-color: {HTB_GREEN_GLOW};
    outline: none;
}}

/* Checkbox - NO BORDER */
QCheckBox {{
    spacing: 10px;
    font-size: 14px;
    border: none;
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: none;
    border-radius: 4px;
    background-color: {HTB_BG_INPUT};
}}

QCheckBox::indicator:hover {{
    background-color: {HTB_BG_HOVER};
}}

QCheckBox::indicator:checked {{
    background-color: {HTB_GREEN};
}}

/* Tables - solo lectura, adaptables */
QTableWidget {{
    background-color: {HTB_BG_CARD};
    alternate-background-color: rgba(26, 38, 56, 0.5);
    border: none;
    border-radius: 12px;
    gridline-color: transparent;
    selection-background-color: {HTB_GREEN_GLOW};
}}

QTableWidget::item {{
    padding: 12px 10px;
    border: none;
}}

QHeaderView {{
    border: none;
}}

QHeaderView::section {{
    background-color: rgba(10, 15, 22, 0.6);
    color: {HTB_TEXT_MUTED};
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.5px;
    padding: 12px 10px;
    border: none;
}}

/* Frames - NO BORDER */
QFrame {{
    border: none;
}}

/* Status bar */
QStatusBar {{
    background-color: {HTB_BG_DARK};
    border: none;
    padding: 8px 16px;
}}

/* Message box */
QMessageBox {{
    background-color: {HTB_BG_CARD};
    border: none;
}}

QMessageBox QLabel {{
    color: {HTB_TEXT};
    border: none;
}}
"""

# Top navigation bar
TOP_NAV_STYLE = f"""
QWidget#top_nav {{
    background-color: #0d1320;
    border: none;
    border-bottom: 1px solid rgba(159, 239, 0, 0.12);
}}

QLabel#nav_logo {{
    font-size: 15px;
    font-weight: 800;
    color: {HTB_GREEN};
    letter-spacing: 1.2px;
}}

QPushButton#nav_item {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 18px;
    font-weight: 500;
    font-size: 14px;
    color: {HTB_TEXT_DIM};
}}

QPushButton#nav_item:hover {{
    background-color: rgba(159, 239, 0, 0.08);
    color: {HTB_TEXT};
}}

QPushButton#nav_item:checked {{
    background-color: {HTB_GREEN_GLOW};
    color: {HTB_GREEN};
}}
"""
