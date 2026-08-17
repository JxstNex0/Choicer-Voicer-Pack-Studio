"""
Choicer Voicer Pack Studio - Standalone Edition
Cyber-Cyan Dark Theme Styling & QSS
"""

# Color Palette Constants
COLOR_BG_DARK = "#0e131b"
COLOR_BG_PANEL = "#141a24"
COLOR_BG_CARD = "#1a2230"
COLOR_BG_INPUT = "#111722"

COLOR_CYAN_PRIMARY = "#58c8db"
COLOR_CYAN_HOVER = "#7ce0f2"
COLOR_CYAN_PRESSED = "#3ba3b5"

COLOR_ACCENT_ORANGE = "#e67e22"
COLOR_ACCENT_RED = "#e74c3c"
COLOR_ACCENT_GREEN = "#2ecc71"
COLOR_ACCENT_YELLOW = "#f1c40f"

COLOR_TEXT_WHITE = "#f0f6fc"
COLOR_TEXT_MUTED = "#8b949e"
COLOR_BORDER = "#253346"

# Distinct Character Colors
CHARACTER_COLORS = [
    "#58c8db",  # Cyan
    "#e67e22",  # Orange
    "#9b59b6",  # Purple
    "#2ecc71",  # Green
    "#e74c3c",  # Red
    "#f1c40f",  # Yellow
    "#1abc9c",  # Turquoise
    "#3498db",  # Blue
    "#fd79a8",  # Pink
    "#00cec9",  # Mint
]


def get_character_color(index: int) -> str:
    return CHARACTER_COLORS[index % len(CHARACTER_COLORS)]


APP_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_WHITE};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}}

QWidget {{
    color: {COLOR_TEXT_WHITE};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
}}

QFrame#PanelFrame, QWidget#PanelWidget {{
    background-color: {COLOR_BG_PANEL};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
}}

/* === BUTTONS === */
QPushButton {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 5px;
    padding: 6px 12px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: #243042;
    border-color: {COLOR_CYAN_PRIMARY};
}}

QPushButton:pressed {{
    background-color: {COLOR_CYAN_PRESSED};
    color: #000000;
}}

QPushButton:disabled {{
    background-color: #121822;
    color: #505a66;
    border-color: #1a2230;
}}

QPushButton#PrimaryButton {{
    background-color: {COLOR_CYAN_PRIMARY};
    color: #0c1219;
    border: none;
}}

QPushButton#PrimaryButton:hover {{
    background-color: {COLOR_CYAN_HOVER};
}}

QPushButton#PrimaryButton:pressed {{
    background-color: {COLOR_CYAN_PRESSED};
}}

QPushButton#DangerButton {{
    background-color: #441818;
    color: #ff8888;
    border: 1px solid #772222;
}}

QPushButton#DangerButton:hover {{
    background-color: #662020;
    border-color: {COLOR_ACCENT_RED};
}}

/* === INPUTS & LINE EDITS === */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {COLOR_BG_INPUT};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: {COLOR_CYAN_PRIMARY};
    selection-color: #000000;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 1px solid {COLOR_CYAN_PRIMARY};
}}

/* === SLIDERS === */
QSlider::groove:horizontal {{
    border: 1px solid {COLOR_BORDER};
    height: 6px;
    background: {COLOR_BG_INPUT};
    border-radius: 3px;
}}

QSlider::sub-page:horizontal {{
    background: {COLOR_CYAN_PRIMARY};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: #ffffff;
    border: 2px solid {COLOR_CYAN_PRIMARY};
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLOR_CYAN_HOVER};
}}

/* === SCROLLBARS === */
QScrollBar:vertical {{
    background: {COLOR_BG_DARK};
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: #243042;
    min-height: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLOR_CYAN_PRIMARY};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {COLOR_BG_DARK};
    height: 8px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: #243042;
    min-width: 20px;
    border-radius: 4px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLOR_CYAN_PRIMARY};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* === MENUS & POPUPS === */
QMenu {{
    background-color: {COLOR_BG_PANEL};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 20px 6px 12px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLOR_CYAN_PRIMARY};
    color: #000000;
}}

QMenu::separator {{
    height: 1px;
    background: {COLOR_BORDER};
    margin: 4px 8px;
}}

/* === SPLITTERS === */
QSplitter::handle {{
    background-color: #1c2738;
}}

QSplitter::handle:horizontal {{
    width: 6px;
    margin: 0px 1px;
    border-radius: 3px;
}}

QSplitter::handle:vertical {{
    height: 6px;
    margin: 1px 0px;
    border-radius: 3px;
}}

QSplitter::handle:hover {{
    background-color: {COLOR_CYAN_PRIMARY};
}}

QSplitter::handle:pressed {{
    background-color: {COLOR_CYAN_HOVER};
}}

/* === TOOLTIPS & STATUS === */
QToolTip {{
    background-color: {COLOR_BG_CARD};
    color: {COLOR_TEXT_WHITE};
    border: 1px solid {COLOR_CYAN_PRIMARY};
    padding: 4px 8px;
    border-radius: 4px;
}}

QStatusBar {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_MUTED};
    border-top: 1px solid {COLOR_BORDER};
}}
"""
