"""
Synvox visual identity: design tokens + the Qt stylesheet.

Palette (sampled from the brand reference image):
    Ink     #0D1311  near-black green, the canvas
    Cream   #F6EECA  warm cream, the single "light" colour
Everything else is derived from those two so the UI stays monochrome-warm.

Like Raining Md, the neutral steps (panel, line, muted...) are plain mixes of Ink and Cream,
so a new surface can never drift off-brand. Forest is the one Synvox-only accent: it tints
the ambient glow behind the glass surfaces.

Design language: iOS-like. Big type, generous spacing, pill shapes, translucent "glass" surfaces.
"""
import os

from PySide6.QtGui import QColor, QFont

from . import paths

# ---- core palette -------------------------------------------------
INK = QColor("#0D1311")          # window / canvas
CREAM = QColor("#F6EECA")        # primary brand colour: text, accents, primary button
CREAM_HI = QColor("#FFF8DA")     # hover state for cream surfaces
CREAM_DIM = QColor("#CFC699")    # secondary cream (muted accents)

# ---- derived surfaces --------------------------------------------
SURFACE = QColor("#141C19")      # cards, popups
SURFACE_HI = QColor("#1B2622")   # raised surface
FOREST = QColor("#2B4A3B")       # ambient glow
FOREST_DEEP = QColor("#16261F")  # deep glow


def mix(a, b, t):
    """Blend colour a towards b by t (0..1), same recipe as Raining Md's Theme."""
    return QColor(round(a.red() + (b.red() - a.red()) * t),
                  round(a.green() + (b.green() - a.green()) * t),
                  round(a.blue() + (b.blue() - a.blue()) * t))


# ---- tonal ramp (Ink -> Cream), borrowed from Raining Md ----------
PANEL = mix(INK, CREAM, 0.05)    # resting cards
PANEL2 = mix(INK, CREAM, 0.09)   # raised cards
HOVER = mix(INK, CREAM, 0.10)
PRESS = mix(INK, CREAM, 0.17)
LINE = mix(INK, CREAM, 0.15)     # hairlines
DIM = mix(INK, CREAM, 0.30)
MUTED = mix(INK, CREAM, 0.50)    # captions, placeholders
SOFT = mix(INK, CREAM, 0.74)     # secondary text

# ---- feedback -----------------------------------------------------
DANGER = QColor("#E0785A")       # warm terracotta, readable on ink

# ---- type scale (px) ---------------------------------------------
T_LARGE = 40      # screen title
T_TITLE = 24      # card titles, counts
T_BODY = 16       # inputs, buttons, table
T_CAPTION = 13    # hints, column headers

# ---- shape --------------------------------------------------------
R_CARD = 28
R_FIELD = 23      # half of the 46px field height: a pill
FIELD_H = 46
BTN_H = 46

FONT_FAMILIES = ["SF Pro Display", "Segoe UI Variable Display", "Segoe UI", "Inter",
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


CHEVRON = paths.asset("chevron.png").replace(os.sep, "/")

STYLE = f"""
QToolTip {{
    background: {SURFACE_HI.name()}; color: {CREAM.name()};
    border: 1px solid {LINE.name()}; border-radius: 10px; padding: 6px 10px;
}}
QLabel {{ background: transparent; }}

QLineEdit, QComboBox {{
    background: {css(CREAM, 0.07)};
    color: {CREAM.name()};
    border: 1px solid {css(CREAM, 0.14)};
    border-radius: {R_FIELD}px;
    padding: 0 20px;
    min-height: {FIELD_H - 2}px;
    font-size: {T_BODY}px;
    selection-background-color: {CREAM.name()};
    selection-color: {INK.name()};
}}
QLineEdit:hover, QComboBox:hover {{ background: {css(CREAM, 0.10)}; }}
QLineEdit:focus, QComboBox:focus {{
    background: {css(CREAM, 0.10)};
    border: 2px solid {css(CREAM, 0.85)};
    padding: 0 19px;
}}
QComboBox::drop-down {{ border: none; width: 40px; }}
QComboBox::down-arrow {{ image: url({CHEVRON}); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE_HI.name()}; color: {CREAM.name()};
    border: 1px solid {LINE.name()}; border-radius: 16px;
    padding: 6px; outline: 0;
    selection-background-color: {css(CREAM, 0.16)}; selection-color: {CREAM_HI.name()};
}}

QTableWidget {{
    background: transparent;
    alternate-background-color: transparent;
    color: {CREAM.name()};
    border: none;
    gridline-color: transparent;
    outline: 0;
    selection-background-color: {css(CREAM, 0.14)};
    selection-color: {CREAM_HI.name()};
}}
QTableWidget::item {{ padding: 0 12px; }}
QTableWidget QLineEdit {{
    border-radius: 12px; padding: 0 10px; min-height: 34px; font-size: {T_BODY}px;
}}
QHeaderView {{ background: transparent; }}
QHeaderView::section {{
    background: transparent; color: {MUTED.name()}; border: none;
    border-bottom: 1px solid {css(CREAM, 0.14)};
    padding: 0 12px; font-size: {T_CAPTION}px; font-weight: 600;
}}
QTableCornerButton::section {{ background: transparent; border: none; }}

QScrollBar:horizontal, QScrollBar:vertical {{ background: transparent; border: none; margin: 0; }}
QScrollBar:horizontal {{ height: 12px; }} QScrollBar:vertical {{ width: 12px; }}
QScrollBar::handle {{
    background: {css(CREAM, 0.22)}; border-radius: 3px; min-width: 40px; min-height: 40px; margin: 3px;
}}
QScrollBar::handle:hover {{ background: {css(CREAM, 0.5)}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{
    background: none; border: none;
}}
"""
