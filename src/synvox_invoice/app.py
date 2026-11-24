import math
import os
import threading
import time
from datetime import datetime

from PySide6.QtCore import (QEasingCurve, QEvent, QPointF, QPropertyAnimation, QRectF, QSize, Qt,
                            QTimer, QVariantAnimation, Signal)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QKeySequence, QLinearGradient,
                           QPainter, QPainterPath, QPen, QRadialGradient, QShortcut)
from PySide6.QtWidgets import (QAbstractButton, QAbstractItemView, QApplication, QComboBox,
                               QFileDialog, QFrame, QGraphicsDropShadowEffect,
                               QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QSizeGrip, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from . import APP_NAME, __version__, core, ocr, paths
from .theme import (BTN_H, CREAM, CREAM_DIM, CREAM_HI, DANGER, FIELD_H, FOREST, FOREST_DEEP, INK,
                    MUTED, R_CARD, SOFT, STYLE, SURFACE, T_BODY, T_CAPTION, T_LARGE, T_TITLE, css,
                    font, mix, rgba)

TIPOS = ["NF", "CTE", "Serviço", "Fatura"]


# =====================
# SYNVOX MARK (vector, drawn at any size)
# =====================
def mark_path(cx, cy, r):
    """The Synvox 'S': two stacked arcs, one continuous stroke. r = radius of each arc."""
    upper = QRectF(cx - r, cy - 2 * r, 2 * r, 2 * r)
    lower = QRectF(cx - r, cy, 2 * r, 2 * r)
    p = QPainterPath()
    p.arcMoveTo(upper, 30)
    p.arcTo(upper, 30, 240)      # up and over to the left, ends at the middle
    p.arcTo(lower, 90, -240)     # down and round to the right, ends bottom-left
    return p


class LogoMark(QWidget):
    """Rounded square frame + S mark + SYNVOX wordmark."""

    def __init__(self, height=56):
        super().__init__()
        self._h = height
        self._word_font = font(int(height * 0.50), QFont.Black)
        text_w = QFontMetrics(self._word_font).horizontalAdvance("SYNVOX")
        self.setFixedSize(int(height * 1.22 + text_w + 6), height)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self._h
        frame = QRectF(1.5, 1.5, h - 3, h - 3)
        p.setPen(QPen(CREAM, max(2.0, h * 0.045)))
        p.setBrush(Qt.NoBrush)
        p.drawRoundedRect(frame, h * 0.24, h * 0.24)

        r = h * 0.14
        pen = QPen(CREAM, h * 0.075, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        p.drawPath(mark_path(h / 2, h / 2, r))

        p.setPen(CREAM)
        p.setFont(self._word_font)
        p.drawText(QRectF(h + h * 0.22, 0, self.width() - h, h), Qt.AlignLeft | Qt.AlignVCenter,
                   "SYNVOX")


# =====================
# GLASS PRIMITIVES
# =====================
class HoverMixin:
    """Smooth 0..1 hover value that widgets read while painting."""

    def _init_hover(self):
        self._hover = 0.0
        self._hover_anim = None
        self._kb_focus = False        # focus ring only for keyboard users, never after a click

    def focusInEvent(self, e):
        self._kb_focus = e.reason() in (Qt.TabFocusReason, Qt.BacktabFocusReason,
                                        Qt.ShortcutFocusReason)
        self.update()
        super().focusInEvent(e)

    def focusOutEvent(self, e):
        self._kb_focus = False
        self.update()
        super().focusOutEvent(e)

    def _go(self, end, ms=160):
        if self._hover_anim:
            self._hover_anim.stop()
        a = QVariantAnimation(self)
        a.setStartValue(float(self._hover))
        a.setEndValue(float(end))
        a.setDuration(ms)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.valueChanged.connect(self._on_hover)
        self._hover_anim = a
        a.start()

    def _on_hover(self, v):
        self._hover = v
        self.update()

    def enterEvent(self, e):
        self._go(1)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._go(0, 220)
        super().leaveEvent(e)


def glass_fill(rect, h, top=34, bottom=14, lift=30):
    """Frosted-glass fill: cream veil, brighter at the top edge, brighter on hover."""
    g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    g.setColorAt(0, rgba(CREAM, top + lift * h))
    g.setColorAt(1, rgba(CREAM, bottom + lift * 0.7 * h))
    return g


def glass_edge(rect, h, width=1.0, top=90, bottom=24):
    """Hairline that catches light at the top, like the rim of a glass pane."""
    g = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    g.setColorAt(0, rgba(CREAM, top + 60 * h))
    g.setColorAt(1, rgba(CREAM, bottom + 30 * h))
    return QPen(QBrush(g), width)


class GlassButton(HoverMixin, QPushButton):
    """Pill button. kind='glass' is translucent, kind='primary' is solid cream with a soft glow."""

    def __init__(self, text="", kind="glass", height=BTN_H, px=T_BODY, weight=QFont.DemiBold,
                 hpad=26, circle=False):
        super().__init__(text)
        self.kind = kind
        self._font = font(px, weight)
        self._hpad = hpad
        self._circle = circle
        self.setFont(self._font)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        if circle:
            self.setFixedSize(height, height)
        else:
            self.setFixedHeight(height)
        self._init_hover()

        self._fx = QGraphicsDropShadowEffect(self)
        if kind == "primary":
            self._fx.setColor(rgba(CREAM, 120))
            self._fx.setOffset(0, 6)
            self._blur = 34
        else:
            self._fx.setColor(QColor(0, 0, 0, 110))
            self._fx.setOffset(0, 5)
            self._blur = 22
        self._fx.setBlurRadius(self._blur)
        self.setGraphicsEffect(self._fx)

    def setText(self, text):
        super().setText(text)
        self.updateGeometry()

    def sizeHint(self):
        if self._circle:
            return QSize(self.height(), self.height())
        w = QFontMetrics(self._font).horizontalAdvance(self.text()) + 2 * self._hpad
        return QSize(w, self.height())

    def minimumSizeHint(self):
        return self.sizeHint()

    def _on_hover(self, v):
        self._fx.setBlurRadius(self._blur + 14 * v)
        super()._on_hover(v)

    def changeEvent(self, e):
        if e.type() == QEvent.EnabledChange:
            self._fx.setEnabled(self.isEnabled())
        super().changeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self._hover
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        if self.isDown():                                   # press = slight shrink
            c = rect.center()
            p.translate(c)
            p.scale(0.97, 0.97)
            p.translate(-c)
        if not self.isEnabled():
            p.setOpacity(0.38)
        r = rect.height() / 2

        if self.kind == "primary":
            fill = CREAM_DIM if self.isDown() else mix(CREAM, CREAM_HI, h)
            p.setPen(Qt.NoPen)
            p.setBrush(fill)
            p.drawRoundedRect(rect, r, r)
            sheen = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            sheen.setColorAt(0, QColor(255, 255, 255, 110))
            sheen.setColorAt(0.55, QColor(255, 255, 255, 0))
            p.setBrush(sheen)
            p.drawRoundedRect(rect, r, r)
            text_color = INK
        else:
            p.setBrush(glass_fill(rect, h))
            p.setPen(glass_edge(rect, h))
            p.drawRoundedRect(rect, r, r)
            text_color = mix(CREAM, CREAM_HI, h)

        if self._kb_focus:
            ring = QPen(rgba(CREAM, 150), 2)
            p.setPen(ring)
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect.adjusted(-1.5, -1.5, 1.5, 1.5), r + 1.5, r + 1.5)

        p.setPen(text_color)
        p.setFont(self._font)
        p.drawText(rect, Qt.AlignCenter, self.text())


class Switch(HoverMixin, QAbstractButton):
    """iOS-style toggle. On = cream track with an ink knob, off = glass track."""

    def __init__(self):
        super().__init__()
        self.setCheckable(True)
        self.setFixedSize(62, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self._init_hover()
        self._pos = 0.0
        self._pos_anim = None
        self.toggled.connect(self._slide)

    def _slide(self, on):
        end = 1.0 if on else 0.0
        if not self.isVisible():
            self._pos = end
            self.update()
            return
        if self._pos_anim:
            self._pos_anim.stop()
        a = QVariantAnimation(self)
        a.setStartValue(float(self._pos))
        a.setEndValue(end)
        a.setDuration(200)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.valueChanged.connect(lambda v: (setattr(self, "_pos", v), self.update()))
        self._pos_anim = a
        a.start()

    def showEvent(self, e):
        if self._pos_anim is None:
            self._pos = 1.0 if self.isChecked() else 0.0
        super().showEvent(e)

    def sizeHint(self):
        return QSize(62, 36)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h, k = self._hover, self._pos
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        r = rect.height() / 2

        track = QRectF(rect)
        off_fill = glass_fill(track, h, top=40, bottom=24, lift=20)
        p.setPen(glass_edge(track, h))
        p.setBrush(off_fill)
        p.drawRoundedRect(track, r, r)
        if k > 0:
            p.setPen(Qt.NoPen)
            p.setBrush(rgba(mix(CREAM, CREAM_HI, h), 255 * k))
            p.drawRoundedRect(track, r, r)

        pad = 4
        d = rect.height() - 2 * pad
        x = rect.left() + pad + (rect.width() - 2 * pad - d) * k
        knob = QRectF(x, rect.top() + pad, d, d)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 60))
        p.drawEllipse(knob.translated(0, 1.5))
        p.setBrush(mix(CREAM, INK, 0.92 * k) if k > 0.5 else CREAM)
        p.drawEllipse(knob)

        if self._kb_focus:
            p.setPen(QPen(rgba(CREAM, 150), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect.adjusted(-1.5, -1.5, 1.5, 1.5), r + 1.5, r + 1.5)


class GlassCard(QFrame):
    """Translucent rounded container."""

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setBrush(glass_fill(rect, 0, top=16, bottom=7, lift=0))
        p.setPen(glass_edge(rect, 0, top=44, bottom=16))
        p.drawRoundedRect(rect, R_CARD, R_CARD)


# =====================
# DROP ZONE
# =====================
class DropZone(HoverMixin, QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(124)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self._init_hover()
        self._busy = False
        self._busy_left = 0
        self._spin = 0
        self._spinner = QTimer(self)
        self._spinner.timeout.connect(self._tick)

    def _tick(self):
        self._spin = (self._spin + 9) % 360
        self.update()

    def set_drag(self, on):
        self._go(1 if on else 0, 180)

    def set_busy(self, on, left=0):
        self._busy = on
        self._busy_left = left
        if on and not self._spinner.isActive():
            self._spinner.start(30)
        elif not on:
            self._spinner.stop()
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.rect().contains(e.position().toPoint()):
            self.clicked.emit()

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.clicked.emit()
        else:
            super().keyPressEvent(e)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        h = self._hover
        rect = QRectF(self.rect()).adjusted(6, 6, -6, -6)
        radius = R_CARD + 4

        # soft halo, grows when hovered or when a file is dragged over
        p.setPen(Qt.NoPen)
        for i in range(1, 5):
            p.setBrush(rgba(CREAM, 16 * h * (5 - i) / 4))
            p.drawRoundedRect(rect.adjusted(-i * 2, -i * 2, i * 2, i * 2), radius + i * 2, radius + i * 2)

        p.setBrush(glass_fill(rect, h, top=26, bottom=10, lift=34))
        p.setPen(glass_edge(rect, h, width=1.4, top=80, bottom=26))
        p.drawRoundedRect(rect, radius, radius)

        # icon bubble
        size = 64
        bx, by = rect.left() + 28, rect.center().y() - size / 2
        bubble = QRectF(bx, by, size, size)
        p.setPen(Qt.NoPen)
        p.setBrush(CREAM if (h > 0.5 or self._busy) else rgba(CREAM, 40))
        p.drawEllipse(bubble)
        ink_on = h > 0.5 or self._busy
        pen = QPen(INK if ink_on else CREAM, 3.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        p.setPen(pen)
        mx, my = bubble.center().x(), bubble.center().y()
        if self._busy:
            ring = bubble.adjusted(17, 17, -17, -17)
            p.setPen(QPen(rgba(INK, 55), 3.2))
            p.drawEllipse(ring)
            p.setPen(pen)
            p.drawArc(ring, int(-self._spin * 16), 100 * 16)
        else:
            p.drawLine(QPointF(mx, my + 12), QPointF(mx, my - 12))
            p.drawLine(QPointF(mx - 10, my - 2), QPointF(mx, my - 12))
            p.drawLine(QPointF(mx + 10, my - 2), QPointF(mx, my - 12))

        tx = bx + size + 24
        if self._busy:
            title = "Reading PDFs…"
            sub = (f"{self._busy_left} left · this only takes a moment" if self._busy_left
                   else "Almost there")
        else:
            title = "Drop invoice PDFs here"
            sub = "or click to browse · several files at once are fine"
        p.setPen(CREAM)
        p.setFont(font(T_TITLE, QFont.DemiBold))
        p.drawText(QRectF(tx, rect.center().y() - 34, rect.right() - tx - 16, 34),
                   Qt.AlignLeft | Qt.AlignVCenter, title)
        p.setPen(SOFT)
        p.setFont(font(T_BODY))
        p.drawText(QRectF(tx, rect.center().y() + 2, rect.right() - tx - 16, 26),
                   Qt.AlignLeft | Qt.AlignVCenter, sub)

        if self._kb_focus:
            p.setPen(QPen(rgba(CREAM, 150), 2))
            p.setBrush(Qt.NoBrush)
            p.drawRoundedRect(rect.adjusted(-3, -3, 3, 3), radius + 3, radius + 3)


# =====================
# LIST ROWS
# =====================
FLAG_ROLE = Qt.UserRole + 1       # True on a required cell that is still empty


class RowDelegate(QStyledItemDelegate):
    """Hairline between rows, and a soft rounded red wash on required cells that are empty."""

    def paint(self, painter, option, index):
        if index.data(FLAG_ROLE):
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(rgba(DANGER, 105))
            painter.drawRoundedRect(QRectF(option.rect).adjusted(6, 9, -6, -9), 12, 12)
            painter.restore()
        super().paint(painter, option, index)
        painter.save()
        painter.setPen(rgba(CREAM, 20))
        painter.drawLine(option.rect.bottomLeft(), option.rect.bottomRight())
        painter.restore()


# =====================
# EMPTY STATE
# =====================
class EmptyState(QWidget):
    """Friendly hint centred over the list while it has no rows."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(6)
        title = QLabel("No invoices yet")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(font(T_TITLE, QFont.DemiBold))
        title.setStyleSheet(f"color: {css(CREAM, 0.9)};")
        sub = QLabel("Drop PDFs above and they will show up here to review.")
        sub.setAlignment(Qt.AlignCenter)
        sub.setFont(font(T_BODY))
        sub.setStyleSheet(f"color: {MUTED.name()};")
        lay.addWidget(title)
        lay.addWidget(sub)


# =====================
# TOAST
# =====================
class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFont(font(T_BODY, QFont.Medium))
        self.fx = QGraphicsOpacityEffect(self)
        self.fx.setOpacity(0)
        self.setGraphicsEffect(self.fx)
        self.anim = QPropertyAnimation(self.fx, b"opacity", self)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(lambda: self._fade(0.0, 300))
        self.hide()

    def _fade(self, end, ms):
        self.anim.stop()
        self.anim.setStartValue(self.fx.opacity())
        self.anim.setEndValue(end)
        self.anim.setDuration(ms)
        self.anim.start()

    def show_message(self, text, error=False, ms=3200):
        border = DANGER.name() if error else css(CREAM, 0.30)
        self.setStyleSheet(f"""
            QLabel {{
                background: rgba(27,38,34,240); color: {CREAM.name()};
                border: 1px solid {border}; border-radius: 26px; padding: 15px 30px;
            }}
        """)
        self.setText(text)
        self.setMaximumWidth(max(320, self.parentWidget().width() - 160))
        self.setWordWrap(False)
        self.adjustSize()
        par = self.parentWidget()
        self.move((par.width() - self.width()) // 2, par.height() - 150)
        self.show()
        self.raise_()
        self._fade(1.0, 180)
        self.timer.start(ms)


# =====================
# MAIN WINDOW
# =====================
FILE_COL = 0                      # extra first column (source PDF), not exported
COL_PX = [170, 120, 112, 120, 125, 280, 130, 120, 135, 120, 108, 112, 135, 220]
GLOW_BAND = 320                   # height of the animated ambient glow at the top of the window


class App(QWidget):
    parsed = Signal(str, list, list, bool)   # path, row, missing, read_with_ocr
    failed = Signal(str, str)                # path, error
    ocr_started = Signal(str)                # path
    batch_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        screen = QApplication.primaryScreen().availableGeometry()
        self.resize(min(1320, screen.width() - 40), min(880, screen.height() - 40))
        self.setMinimumSize(1000, 700)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLE)

        self.drag_pos = None
        self._shown_once = False
        self._pending = 0
        self._paths = set()
        self._t0 = time.monotonic()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 22, 40, 26)
        layout.setSpacing(16)

        layout.addWidget(self.top_bar())
        layout.addWidget(self.title_block())

        self.drop = DropZone()
        self.drop.clicked.connect(self.browse)
        layout.addWidget(self.drop)
        layout.addLayout(self.controls())
        layout.addWidget(self.build_list(), 1)
        layout.addLayout(self.footer())

        self.toast = Toast(self)
        self.grip = QSizeGrip(self)
        self.grip.setFixedSize(18, 18)
        self.grip.setStyleSheet("background: transparent;")
        self.parsed.connect(self.on_parsed)
        self.failed.connect(self.on_failed)
        self.ocr_started.connect(self.on_ocr_started)
        self.batch_done.connect(self.on_batch_done)

        glow = QTimer(self)
        glow.timeout.connect(lambda: self.update(0, 0, self.width(), GLOW_BAND))
        glow.start(40)
        self._sync_actions()

    # ---------- top bar ----------
    def top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(44)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)
        lay.addWidget(LogoMark(34), 0, Qt.AlignVCenter)
        lay.addStretch()

        version = QLabel(f"v{__version__}")
        version.setFont(font(T_CAPTION, QFont.Medium))
        version.setStyleSheet(f"color: {MUTED.name()};")
        lay.addWidget(version)
        lay.addSpacing(6)

        btn_min = GlassButton("—", height=38, px=15, circle=True)
        btn_close = GlassButton("✕", height=38, px=15, circle=True)
        for b in (btn_min, btn_close):
            b.setFocusPolicy(Qt.NoFocus)             # window chrome, not part of the tab order
        btn_min.setToolTip("Minimize")
        btn_close.setToolTip("Close")
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.fade_close)
        lay.addWidget(btn_min)
        lay.addWidget(btn_close)
        return bar

    # ---------- large title ----------
    def title_block(self):
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(2, 6, 0, 0)
        lay.setSpacing(0)

        hour = datetime.now().hour
        greeting = ("Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening")
        hello = QLabel(greeting)
        hello.setFont(font(T_BODY, QFont.Medium))
        hello.setStyleSheet(f"color: {SOFT.name()};")

        title = QLabel("Invoice Extractor")
        title.setFont(font(T_LARGE, QFont.Bold))
        title.setStyleSheet(f"color: {CREAM.name()};")

        lay.addWidget(hello)
        lay.addWidget(title)
        return box

    # ---------- controls ----------
    def controls(self):
        row = QHBoxLayout()
        row.setSpacing(18)

        def field(caption, widget, tip=None):
            col = QVBoxLayout()
            col.setSpacing(7)
            l = QLabel(caption)
            l.setFont(font(T_CAPTION, QFont.DemiBold))
            l.setStyleSheet(f"color: {MUTED.name()}; padding-left: 6px;")
            col.addWidget(l)
            col.addWidget(widget)
            if tip:
                widget.setToolTip(tip)
            return col

        self.in_user = QLineEdit()
        self.in_user.setPlaceholderText(core.DEFAULT_LANCADO_POR)
        self.in_user.setFixedSize(250, FIELD_H)
        self.in_user.setText(core.DEFAULT_LANCADO_POR)

        self.in_tipo = QComboBox()
        self.in_tipo.setEditable(True)
        self.in_tipo.addItems(TIPOS)
        self.in_tipo.setFixedSize(190, FIELD_H)

        self.sw_ocr = Switch()
        self.sw_ocr.setChecked(ocr.enabled())
        self.sw_ocr.toggled.connect(self._ocr_toggled)
        self.lbl_ocr = QLabel("Read scanned PDFs")
        self.lbl_ocr.setFont(font(T_BODY, QFont.Medium))
        ocr_row = QWidget()
        ocr_row.setFixedHeight(FIELD_H)
        ocr_lay = QHBoxLayout(ocr_row)
        ocr_lay.setContentsMargins(6, 0, 0, 0)
        ocr_lay.setSpacing(12)
        ocr_lay.addWidget(self.sw_ocr)
        ocr_lay.addWidget(self.lbl_ocr)
        ocr_lay.addStretch()
        self._ocr_toggled(self.sw_ocr.isChecked())

        self.btn_rm = GlassButton("Remove selected")
        self.btn_clear = GlassButton("Clear all")
        self.btn_rm.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)

        row.addLayout(field("LANÇADO POR", self.in_user))
        row.addLayout(field("TIPO OPERAÇÃO (PADRÃO)", self.in_tipo))
        row.addLayout(field("OCR", ocr_row))
        row.addStretch()
        actions = QHBoxLayout()
        actions.setSpacing(10)
        actions.addWidget(self.btn_rm)
        actions.addWidget(self.btn_clear)
        bottom = QVBoxLayout()
        bottom.addSpacing(T_CAPTION + 7 + 4)       # align the buttons with the fields, not the captions
        bottom.addLayout(actions)
        row.addLayout(bottom)
        return row

    def _ocr_toggled(self, on):
        tip = ("Read scanned or image-only PDFs with OCR (slower)." if on
               else "OCR is off: scanned PDFs will be rejected.")
        self.sw_ocr.setToolTip(tip)
        self.lbl_ocr.setToolTip(tip)
        self.lbl_ocr.setStyleSheet(f"color: {CREAM.name() if on else SOFT.name()};")

    # ---------- list ----------
    def build_list(self):
        card = GlassCard()
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.addWidget(self.build_table())
        return card

    def build_table(self):
        t = QTableWidget(0, len(core.HEADERS) + 1)
        labels = ["SOURCE PDF"] + [" ".join(h.split()) for h in core.HEADERS]
        t.setHorizontalHeaderLabels(labels)
        t.setAlternatingRowColors(False)
        t.setShowGrid(False)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                          | QAbstractItemView.AnyKeyPressed)
        t.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        t.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(54)
        t.horizontalHeader().setHighlightSections(False)
        t.horizontalHeader().setFixedHeight(46)
        t.setFont(font(15))
        t.setFrameShape(QFrame.NoFrame)
        t.setFocusPolicy(Qt.StrongFocus)
        t.setWordWrap(False)
        t.setTextElideMode(Qt.ElideRight)
        t.setItemDelegate(RowDelegate(t))

        # COL_PX are minimum widths; a column also grows to fit its own header
        head_fm = QFontMetrics(font(T_CAPTION, QFont.DemiBold))
        for i, label in enumerate(labels):
            t.setColumnWidth(i, max(COL_PX[i], head_fm.horizontalAdvance(label) + 40))
            c = i - 1                                   # same alignment as the data below it
            if i == FILE_COL:
                al = Qt.AlignLeft
            elif c == core.VAL:
                al = Qt.AlignRight
            elif c in core.DATE_COLS or c in (core.NF, core.PED, core.CTE, core.TIPO):
                al = Qt.AlignCenter
            else:
                al = Qt.AlignLeft
            t.horizontalHeaderItem(i).setTextAlignment(al | Qt.AlignVCenter)
        t.itemChanged.connect(self.on_item_changed)
        t.itemSelectionChanged.connect(self._sync_actions)

        sc = QShortcut(QKeySequence.Delete, t)
        sc.setContext(Qt.WidgetShortcut)
        sc.activated.connect(self.remove_selected)

        self.empty = EmptyState(t.viewport())
        t.viewport().installEventFilter(self)
        self.table = t
        return t

    def eventFilter(self, obj, ev):
        if hasattr(self, "table") and obj is self.table.viewport() and ev.type() == QEvent.Resize:
            self.empty.setGeometry(self.table.viewport().rect())
        return super().eventFilter(obj, ev)

    # ---------- footer ----------
    def footer(self):
        row = QHBoxLayout()
        row.setSpacing(20)
        left = QVBoxLayout()
        left.setSpacing(2)
        self.summary = QLabel("")
        self.summary.setFont(font(T_TITLE, QFont.DemiBold))
        self.hint = QLabel("")
        self.hint.setFont(font(T_CAPTION))
        self.hint.setStyleSheet(f"color: {MUTED.name()};")
        left.addWidget(self.summary)
        left.addWidget(self.hint)

        self.btn_export = GlassButton("Export XLSX", kind="primary", height=58, px=18,
                                      weight=QFont.Bold, hpad=46)
        self.btn_export.clicked.connect(self.export)
        row.addLayout(left)
        row.addStretch()
        row.addWidget(self.btn_export)
        self.refresh_summary()
        return row

    # ---------- cell flagging ----------
    def _flag(self, item):
        col = item.column() - 1
        bad = col in core.REQUIRED and not item.text().strip()
        item.setData(FLAG_ROLE, bad)

    def on_item_changed(self, item):
        if item.column() == FILE_COL:
            return
        self.table.blockSignals(True)
        self._flag(item)
        self.table.blockSignals(False)
        self.refresh_summary()

    def _sync_actions(self):
        """Only offer what makes sense right now."""
        n = self.table.rowCount() if hasattr(self, "table") else 0
        sel = bool(self.table.selectedIndexes()) if n else False
        self.btn_rm.setEnabled(sel)
        self.btn_clear.setEnabled(n > 0)
        self.btn_export.setEnabled(n > 0)
        if hasattr(self, "empty"):
            self.empty.setVisible(n == 0)

    def refresh_summary(self):
        n = self.table.rowCount() if hasattr(self, "table") else 0
        total = 0.0
        for r in range(n):
            it = self.table.item(r, core.VAL + 1)
            try:
                total += core.parse_money(it.text()) or 0.0 if it else 0.0
            except ValueError:
                pass
        if n:
            self.summary.setText(f"{n} invoice{'s' if n != 1 else ''}  ·  R$ {core.fmt_money(total)}")
            self.summary.setStyleSheet(f"color: {CREAM.name()};")
            self.hint.setText("Double-click a cell to edit · cells in red need attention")
        else:
            self.summary.setText("Nothing to export yet")
            self.summary.setStyleSheet(f"color: {MUTED.name()};")
            self.hint.setText("Add a PDF to get started")
        self._sync_actions()

    # ---------- adding files ----------
    def browse(self):
        paths_, _ = QFileDialog.getOpenFileNames(self, "Select invoice PDFs", "", "PDF (*.pdf)")
        if paths_:
            self.add_files(paths_)

    def add_files(self, files):
        new = [p for p in files if p.lower().endswith(".pdf") and p not in self._paths]
        if not new:
            self.toast.show_message("Those PDFs are already in the list", error=True)
            return
        self._paths.update(new)
        self._pending += len(new)
        self.drop.set_busy(True, self._pending)
        self.toast.show_message(f"Reading {len(new)} PDF{'s' if len(new) != 1 else ''}…")
        user, tipo = self.in_user.text().strip(), self.in_tipo.currentText().strip()
        use_ocr = self.sw_ocr.isChecked()
        threading.Thread(target=self._worker, args=(new, user, tipo, use_ocr), daemon=True).start()

    def _worker(self, files, user, tipo, use_ocr):
        for p in files:
            try:
                row, missing, used = core.extract_invoice(
                    p, user, tipo, dump_dir=paths.logs_dir(), use_ocr=use_ocr,
                    on_ocr=lambda p=p: self.ocr_started.emit(p))
                self.parsed.emit(p, row, missing, used)
            except Exception as err:
                self.failed.emit(p, str(err))
        self.batch_done.emit()

    def on_ocr_started(self, path):
        self.toast.show_message(f"{os.path.basename(path)}: running OCR, this can take a few seconds…",
                                ms=6000)

    def _one_done(self):
        self._pending = max(0, self._pending - 1)
        if self._pending:
            self.drop.set_busy(True, self._pending)

    def on_parsed(self, path, row, missing, used_ocr=False):
        self._one_done()
        t = self.table
        t.blockSignals(True)
        r = t.rowCount()
        t.insertRow(r)
        f = QTableWidgetItem(os.path.basename(path) + ("  · OCR" if used_ocr else ""))
        f.setFlags(f.flags() & ~Qt.ItemIsEditable)
        f.setToolTip(path + ("\nRead with OCR: please double-check the values." if used_ocr else ""))
        f.setForeground(rgba(CREAM, 150))
        f.setData(Qt.UserRole, path)
        t.setItem(r, FILE_COL, f)
        for c, text in enumerate(row):
            it = QTableWidgetItem(text)
            if c == core.VAL:
                it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            elif c in core.DATE_COLS or c in (core.NF, core.PED, core.CTE, core.TIPO):
                it.setTextAlignment(Qt.AlignCenter)
            if missing and c in core.REQUIRED and not text:
                it.setToolTip("Not found in the PDF. Please fill in.")
            t.setItem(r, c + 1, it)
            self._flag(it)
        t.blockSignals(False)
        t.scrollToBottom()
        self.refresh_summary()
        if missing:
            self.toast.show_message(f"{os.path.basename(path)}: check {', '.join(missing)}", error=True)
        elif used_ocr:
            self.toast.show_message(f"{os.path.basename(path)}: read with OCR, please double-check", ms=4500)

    def on_failed(self, path, err):
        self._one_done()
        self._paths.discard(path)
        self.toast.show_message(f"{os.path.basename(path)}: {err}", error=True, ms=5000)

    def on_batch_done(self):
        self._pending = 0
        self.drop.set_busy(False)

    # ---------- table actions ----------
    def _drop_paths_of_rows(self, rows):
        for r in rows:
            it = self.table.item(r, FILE_COL)
            if it:
                self._paths.discard(it.data(Qt.UserRole))

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        self._drop_paths_of_rows(rows)
        for r in rows:
            self.table.removeRow(r)
        self.refresh_summary()

    def clear_all(self):
        self.table.setRowCount(0)
        self._paths.clear()
        self.refresh_summary()

    def collect_rows(self):
        return [[(self.table.item(r, c + 1).text() if self.table.item(r, c + 1) else "")
                 for c in range(len(core.HEADERS))]
                for r in range(self.table.rowCount())]

    # ---------- export ----------
    def export(self):
        rows = self.collect_rows()
        if not rows:
            self.toast.show_message("Nothing to export yet", error=True)
            return

        # validate first so we can point at the bad cell
        for r, row in enumerate(rows):
            try:
                core.convert_row(row)
            except ValueError as err:
                self.table.selectRow(r)
                self.table.scrollToItem(self.table.item(r, 1))
                self.toast.show_message(f"Row {r + 1} · {err}", error=True, ms=5000)
                return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export XLSX (an existing file will be appended to)", paths.default_export_path(),
            "Excel (*.xlsx)", options=QFileDialog.Option.DontConfirmOverwrite)
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            n, appended = core.export_xlsx(rows, path)
        except PermissionError:
            self.toast.show_message("Can't write the file. Is it open in Excel?", error=True, ms=5000)
            return
        except Exception as err:
            self.toast.show_message(f"Export failed: {err}", error=True, ms=5000)
            return

        self.toast.show_message(f"{n} row(s) {'appended to' if appended else 'saved in'} "
                                f"{os.path.basename(path)}")
        self.clear_all()

    # ---------- window ----------
    def fade_close(self):
        self._close_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._close_anim.setDuration(160)
        self._close_anim.setEndValue(0.0)
        self._close_anim.finished.connect(QApplication.quit)
        self._close_anim.start()

    def showEvent(self, e):
        super().showEvent(e)
        if self._shown_once:
            return
        self._shown_once = True
        self.setWindowOpacity(0.0)
        self._open_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._open_anim.setDuration(350)
        self._open_anim.setEndValue(1.0)
        self._open_anim.start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.grip.move(self.width() - self.grip.width() - 8, self.height() - self.grip.height() - 8)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.monotonic() - self._t0
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)

        clip = QPainterPath()
        clip.addRoundedRect(rect, 30, 30)
        p.fillPath(clip, INK)
        p.setClipPath(clip)

        # ambient light behind the glass: slow, soft, never busy
        def glow(cx, cy, radius, color, alpha):
            g = QRadialGradient(cx, cy, radius)
            g.setColorAt(0, rgba(color, alpha))
            g.setColorAt(1, rgba(color, 0))
            p.fillRect(self.rect(), g)

        glow(w * (0.28 + 0.10 * math.sin(t * 0.5)), 100 + 30 * math.cos(t * 0.4), w * 0.48, FOREST, 235)
        glow(w * (0.84 + 0.05 * math.cos(t * 0.35)), 90 + 20 * math.sin(t * 0.3), w * 0.24, CREAM, 36)
        glow(w * 0.96, h * 0.98, w * 0.36, FOREST_DEEP, 210)
        glow(w * 0.04, h * 0.92, w * 0.24, FOREST, 80)

        p.setClipping(False)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(rgba(CREAM, 26), 1))
        p.drawRoundedRect(rect, 30, 30)

    # ---------- drag & drop of PDFs ----------
    @staticmethod
    def _pdfs(mime):
        return [u.toLocalFile() for u in mime.urls()
                if u.isLocalFile() and u.toLocalFile().lower().endswith(".pdf")]

    def dragEnterEvent(self, e):
        if self._pdfs(e.mimeData()):
            e.acceptProposedAction()
            self.drop.set_drag(True)

    def dragLeaveEvent(self, e):
        self.drop.set_drag(False)

    def dropEvent(self, e):
        self.drop.set_drag(False)
        files = self._pdfs(e.mimeData())
        if files:
            e.acceptProposedAction()
            self.add_files(files)

    # ---------- drag window ----------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag_pos = e.globalPosition().toPoint()

    def mouseMoveEvent(self, e):
        if self.drag_pos is not None:
            delta = e.globalPosition().toPoint() - self.drag_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.drag_pos = e.globalPosition().toPoint()

    def mouseReleaseEvent(self, e):
        self.drag_pos = None
