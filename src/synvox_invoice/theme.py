"""
Synvox visual identity: design tokens + the Qt stylesheet.

Palette (sampled from the brand reference image):
    Ink     #0D1311  near-black green, the canvas
    Cream   #F6EECA  warm cream, the single "light" colour
Everything else is derived from those two so the UI stays monochrome-warm.
"""
from PySide6.QtGui import QColor, QFont

# ---- core palette -------------------------------------------------
INK = QColor("#0D1311")          # window / canvas
CREAM = QColor("#F6EECA")        # primary brand colour: text, accents, primary button
CREAM_HI = QColor("#FFF8DA")     # hover state for cream surfaces
CREAM_DIM = QColor("#CFC699")    # secondary cream (muted accents)

# ---- derived surfaces --------------------------------------------
SURFACE = QColor("#141C19")      # cards, popups
SURFACE_HI = QColor("#1B2622")   # raised surface
FOREST = QColor("#2B4A3B")       # glow / table header highlight
FOREST_DEEP = QColor("#16261F")  # table header, deep glow

# ---- feedback -----------------------------------------------------
DANGER = QColor("#E0785A")       # warm terracotta, readable on ink

FONT_FAMILIES = ["Segoe UI Variable Display", "Segoe UI", "Inter",
                 "Helvetica Neue", "Arial"]


def rgba(color, alpha):
    """QColor with a 0-255 alpha."""
    c = QColor(color)
    c.setAlpha(int(alpha))
    return c


def css(color, alpha=1.0):
    """CSS rgba() string from a QColor and a 0-1 alpha."""
    return f"rgba({color.red()},{color.green()},{color.blue()},{alpha})"


def font(px, weight=QFont.Normal, families=FONT_FAMILIES):
    f = QFont()
    f.setFamilies(families)
    f.setPixelSize(px)
    f.setWeight(weight)
    return f


STYLE = f"""
QLineEdit, QComboBox {{
    background: {css(CREAM, 0.06)};
    color: {CREAM.name()};
    border: 1px solid {css(CREAM, 0.16)};
    border-radius: 12px;
    padding: 7px 12px;
    selection-background-color: {CREAM.name()};
    selection-color: {INK.name()};
}}
QLineEdit:focus, QComboBox:focus {{ border: 1px solid {CREAM.name()}; }}
QComboBox QAbstractItemView {{
    background: {SURFACE.name()}; color: {CREAM.name()};
    border: 1px solid {css(CREAM, 0.16)};
    selection-background-color: {CREAM.name()}; selection-color: {INK.name()};
}}
QComboBox::drop-down {{ border: none; width: 22px; }}

QPushButton#ghost {{
    background: {css(CREAM, 0.06)}; color: {css(CREAM, 0.9)};
    border: 1px solid {css(CREAM, 0.16)}; border-radius: 12px; padding: 8px 16px;
}}
QPushButton#ghost:hover {{ background: {css(CREAM, 0.16)}; color: {CREAM_HI.name()}; }}

QPushButton#primary {{
    background: {CREAM.name()};
    color: {INK.name()}; border: none; border-radius: 14px; padding: 11px 26px; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {CREAM_HI.name()}; }}
QPushButton#primary:pressed {{ background: {CREAM_DIM.name()}; }}

QTableWidget {{
    background: {css(CREAM, 0.04)};
    alternate-background-color: {css(CREAM, 0.02)};
    color: {CREAM.name()};
    border: 1px solid {css(CREAM, 0.10)};
    border-radius: 14px;
    gridline-color: {css(CREAM, 0.07)};
    selection-background-color: {css(CREAM, 0.20)};
    selection-color: {CREAM_HI.name()};
}}
QTableWidget QLineEdit {{ border-radius: 4px; padding: 2px 6px; }}
QHeaderView::section {{
    background: {FOREST_DEEP.name()}; color: {CREAM.name()}; border: none;
    border-right: 1px solid {css(CREAM, 0.10)};
    padding: 8px 6px; font-weight: 600;
}}
QTableCornerButton::section {{ background: {FOREST_DEEP.name()}; border: none; }}
QScrollBar:horizontal, QScrollBar:vertical {{ background: transparent; border: none; margin: 0; }}
QScrollBar:horizontal {{ height: 10px; }} QScrollBar:vertical {{ width: 10px; }}
QScrollBar::handle {{ background: {css(CREAM, 0.25)}; border-radius: 5px; min-width: 30px; min-height: 30px; }}
QScrollBar::handle:hover {{ background: {CREAM.name()}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ background: none; border: none; }}
"""
