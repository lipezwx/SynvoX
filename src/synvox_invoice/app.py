import math
import os
import threading
import time
from datetime import datetime

from PySide6.QtCore import (QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, QTimer,
                            QVariantAnimation, Signal)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetrics, QKeySequence, QLinearGradient, QPainter,
                           QPainterPath, QPen, QRadialGradient, QShortcut)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog, QFrame,
                               QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit,
                               QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)

from . import APP_NAME, __version__, core, paths
from .theme import (CREAM, CREAM_HI, DANGER, FOREST, FOREST_DEEP, INK, STYLE, SURFACE, css,
                    font, rgba)

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
# DROP ZONE
# =====================
class DropZone(QWidget):
    clicked = Signal()

    def __init__(self):
        super().__init__()
        self.setFixedHeight(92)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.StrongFocus)
        self._hover = 0.0
        self._anim = None
        self._busy = False

    def _go(self, end, ms=180):
        if self._anim:
            self._anim.stop()
        a = QVariantAnimation(self)
        a.setStartValue(float(self._hover))
        a.setEndValue(float(end))
        a.setDuration(ms)
        a.setEasingCurve(QEasingCurve.OutCubic)
        a.valueChanged.connect(lambda v: (setattr(self, "_hover", v), self.update()))
        self._anim = a
        a.start()

    def set_drag(self, on):
        self._go(1 if on else 0)

    def set_busy(self, on):
        self._busy = on
        self.update()

    def enterEvent(self, e):
        self._go(1)

    def leaveEvent(self, e):
        self._go(0, 220)

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
        rect = QRectF(self.rect()).adjusted(3, 3, -3, -3)

        p.setPen(Qt.NoPen)
        for i in range(1, 4):
            p.setBrush(rgba(CREAM, 18 * h * (4 - i) / 3))
            p.drawRoundedRect(rect.adjusted(-i * 2, -i * 2, i * 2, i * 2), 18 + i * 2, 18 + i * 2)

        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0, rgba(FOREST, 90 * h + 30))
        grad.setColorAt(1, rgba(FOREST_DEEP, 150 * h + 40))
        p.setBrush(grad)
        p.setPen(QPen(rgba(CREAM, 60 + 150 * h), 1.5, Qt.DashLine))
        p.drawRoundedRect(rect, 18, 18)

        # icon circle with an upload arrow
        size = 46
        cx, cy = rect.left() + 20, rect.center().y() - size / 2
        p.setPen(Qt.NoPen)
        p.setBrush(CREAM if h > 0.5 else rgba(CREAM, 34))
        p.drawEllipse(QRectF(cx, cy, size, size))
        p.setPen(QPen(INK if h > 0.5 else CREAM, 2.4, Qt.SolidLine, Qt.RoundCap))
        mx, my = cx + size / 2, cy + size / 2
        p.drawLine(QPointF(mx, my + 9), QPointF(mx, my - 9))
        p.drawLine(QPointF(mx - 7, my - 2), QPointF(mx, my - 9))
        p.drawLine(QPointF(mx + 7, my - 2), QPointF(mx, my - 9))

        tx = cx + size + 18
        p.setPen(CREAM)
        p.setFont(font(17, QFont.DemiBold))
        p.drawText(QRectF(tx, rect.top() + 18, rect.width() - tx, 26),
                   Qt.AlignLeft | Qt.AlignVCenter,
                   "Reading PDFs…" if self._busy else "Drop invoice PDFs here")
        p.setPen(rgba(CREAM, 150))
        p.setFont(font(12))
        p.drawText(QRectF(tx, rect.top() + 46, rect.width() - tx, 20),
                   Qt.AlignLeft | Qt.AlignVCenter,
                   "or click to browse · several files at once are fine")


# =====================
# HERO
# =====================
class Hero(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(190)
        self._t0 = time.monotonic()
        timer = QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(33)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(0)

        logo = LogoMark(46)
        layout.addWidget(logo, 0, Qt.AlignHCenter)
        layout.addSpacing(8)

        hour = datetime.now().hour
        greeting = ("Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening")
        hello = QLabel(greeting)
        hello.setAlignment(Qt.AlignCenter)
        hello.setFont(font(14))
        hello.setStyleSheet(f"color: {css(CREAM, 0.7)}; background: transparent;")

        title = QLabel("Invoice Extractor")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(font(32, QFont.Bold))
        title.setStyleSheet(f"color: {CREAM.name()}; background: transparent;")

        subtitle = QLabel("PDF · Extract · Review · Export XLSX")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setFont(font(13))
        subtitle.setStyleSheet(f"color: {css(CREAM, 0.6)}; background: transparent;")

        layout.addWidget(hello)
        layout.addSpacing(2)
        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(subtitle)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        t = time.monotonic() - self._t0

        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 20, 20)
        p.setClipPath(clip)
        p.fillPath(clip, QColor("#101714"))

        def glow(cx, cy, radius, color, alpha):
            g = QRadialGradient(cx, cy, radius)
            g.setColorAt(0, rgba(color, alpha))
            g.setColorAt(1, rgba(color, 0))
            p.fillRect(self.rect(), g)

        glow(w * (0.50 + 0.18 * math.sin(t * 0.6)), h * (0.15 + 0.10 * math.cos(t * 0.5)),
             w * 0.50, FOREST, 210)
        glow(w * (0.18 + 0.08 * math.sin(t * 0.4 + 2)), h * 0.85, w * 0.30, CREAM, 38)
        glow(w * (0.85 + 0.06 * math.cos(t * 0.35)), h * 0.75, w * 0.30, FOREST_DEEP, 200)

        fade = QLinearGradient(0, h * 0.68, 0, h)
        fade.setColorAt(0, rgba(INK, 0))
        fade.setColorAt(1, rgba(INK, 255))
        p.fillRect(self.rect(), fade)


# =====================
# TOAST
# =====================
class Toast(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setFont(font(13, QFont.Medium))
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
        border = DANGER.name() if error else css(CREAM, 0.25)
        self.setStyleSheet(f"""
            QLabel {{
                background: rgba(20,28,25,245); color: {CREAM.name()};
                border: 1px solid {border}; border-radius: 18px; padding: 10px 22px;
            }}
        """)
        self.setText(text)
        self.adjustSize()
        par = self.parentWidget()
        self.move((par.width() - self.width()) // 2, par.height() - 96)
        self.show()
        self.raise_()
        self._fade(1.0, 180)
        self.timer.start(ms)


# =====================
# MAIN WINDOW
# =====================
FILE_COL = 0                      # extra first column (source PDF), not exported
COL_PX = [150, 105, 100, 105, 110, 250, 115, 105, 120, 105, 95, 100, 120, 200]


class App(QWidget):
    parsed = Signal(str, list, list)     # path, row, missing
    failed = Signal(str, str)            # path, error
    batch_done = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(1360, 780)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)
        self.setStyleSheet(STYLE)

        self.drag_pos = None
        self._shown_once = False
        self._pending = 0
        self._paths = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 20)
        layout.setSpacing(12)

        layout.addWidget(self.top_bar())
        layout.addWidget(Hero())

        self.drop = DropZone()
        self.drop.clicked.connect(self.browse)
        layout.addWidget(self.drop)
        layout.addLayout(self.controls())
        layout.addWidget(self.build_table(), 1)
        layout.addLayout(self.footer())

        self.toast = Toast(self)
        self.parsed.connect(self.on_parsed)
        self.failed.connect(self.on_failed)
        self.batch_done.connect(self.on_batch_done)

    # ---------- top bar ----------
    def top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(40)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(0, 0, 0, 0)

        title = QLabel(f"<span style='color:{CREAM.name()}'>●</span>"
                       f"&nbsp;&nbsp;Synvox Invoice Extractor"
                       f"<span style='color:{css(CREAM, 0.4)}'>&nbsp;&nbsp;v{__version__}</span>")
        title.setFont(font(13, QFont.Medium))
        title.setStyleSheet(f"color: {css(CREAM, 0.85)};")
        lay.addWidget(title)
        lay.addStretch()

        btn_min, btn_close = QPushButton("—"), QPushButton("✕")
        btn_min.clicked.connect(self.showMinimized)
        btn_close.clicked.connect(self.fade_close)
        for b, hover, hover_fg in ((btn_min, css(CREAM, 0.16), CREAM_HI.name()),
                                   (btn_close, CREAM.name(), INK.name())):
            b.setFixedSize(38, 28)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {css(CREAM, 0.8)};
                               border: none; border-radius: 9px; }}
                QPushButton:hover {{ background: {hover}; color: {hover_fg}; }}
            """)
            lay.addWidget(b)
        return bar

    # ---------- controls ----------
    def controls(self):
        row = QHBoxLayout()
        row.setSpacing(10)

        def lbl(text):
            l = QLabel(text)
            l.setFont(font(12, QFont.Medium))
            l.setStyleSheet(f"color: {css(CREAM, 0.6)};")
            return l

        self.in_user = QLineEdit()
        self.in_user.setPlaceholderText(core.DEFAULT_LANCADO_POR)
        self.in_user.setFixedWidth(200)
        self.in_user.setText(core.DEFAULT_LANCADO_POR)

        self.in_tipo = QComboBox()
        self.in_tipo.setEditable(True)
        self.in_tipo.addItems(TIPOS)
        self.in_tipo.setFixedWidth(140)

        btn_rm = QPushButton("Remove selected")
        btn_clear = QPushButton("Clear all")
        for b in (btn_rm, btn_clear):
            b.setObjectName("ghost")
            b.setCursor(Qt.PointingHandCursor)
        btn_rm.clicked.connect(self.remove_selected)
        btn_clear.clicked.connect(self.clear_all)

        row.addWidget(lbl("LANÇADO POR"))
        row.addWidget(self.in_user)
        row.addSpacing(8)
        row.addWidget(lbl("TIPO OPERAÇÃO (default)"))
        row.addWidget(self.in_tipo)
        row.addStretch()
        row.addWidget(btn_rm)
        row.addWidget(btn_clear)
        return row

    # ---------- table ----------
    def build_table(self):
        t = QTableWidget(0, len(core.HEADERS) + 1)
        labels = ["SOURCE PDF"] + [" ".join(h.split()) for h in core.HEADERS]
        t.setHorizontalHeaderLabels(labels)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setSelectionMode(QAbstractItemView.ExtendedSelection)
        t.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed
                          | QAbstractItemView.AnyKeyPressed)
        t.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        t.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        t.verticalHeader().setVisible(False)
        t.verticalHeader().setDefaultSectionSize(36)
        t.horizontalHeader().setHighlightSections(False)
        t.horizontalHeader().setFixedHeight(40)
        t.setFont(font(13))
        t.setFrameShape(QFrame.NoFrame)
        for i, w in enumerate(COL_PX):
            t.setColumnWidth(i, w)
        t.itemChanged.connect(self.on_item_changed)

        sc = QShortcut(QKeySequence.Delete, t)
        sc.setContext(Qt.WidgetShortcut)
        sc.activated.connect(self.remove_selected)

        self.table = t
        return t

    def footer(self):
        row = QHBoxLayout()
        self.summary = QLabel("")
        self.summary.setFont(font(12))
        self.summary.setStyleSheet(f"color: {css(CREAM, 0.55)};")
        self.btn_export = QPushButton("Export XLSX")
        self.btn_export.setObjectName("primary")
        self.btn_export.setFont(font(14, QFont.DemiBold))
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.clicked.connect(self.export)
        row.addWidget(self.summary)
        row.addStretch()
        row.addWidget(self.btn_export)
        self.refresh_summary()
        return row

    # ---------- cell flagging ----------
    def _flag(self, item):
        col = item.column() - 1
        bad = col in core.REQUIRED and not item.text().strip()
        item.setBackground(QBrush(rgba(DANGER, 70)) if bad else QBrush())

    def on_item_changed(self, item):
        if item.column() == FILE_COL:
            return
        self.table.blockSignals(True)
        self._flag(item)
        self.table.blockSignals(False)
        self.refresh_summary()

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
            self.summary.setText(f"{n} invoice(s) ready · total R$ {core.fmt_money(total)}"
                                 "  ·  double-click a cell to edit; red cells need attention")
        else:
            self.summary.setText("No invoices yet")

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
        self.drop.set_busy(True)
        self.toast.show_message(f"Reading {len(new)} PDF(s)…")
        user, tipo = self.in_user.text().strip(), self.in_tipo.currentText().strip()
        threading.Thread(target=self._worker, args=(new, user, tipo), daemon=True).start()

    def _worker(self, files, user, tipo):
        for p in files:
            try:
                row, missing = core.extract_invoice(p, user, tipo, dump_dir=paths.logs_dir())
                self.parsed.emit(p, row, missing)
            except Exception as err:
                self.failed.emit(p, str(err))
        self.batch_done.emit()

    def on_parsed(self, path, row, missing):
        t = self.table
        t.blockSignals(True)
        r = t.rowCount()
        t.insertRow(r)
        f = QTableWidgetItem(os.path.basename(path))
        f.setFlags(f.flags() & ~Qt.ItemIsEditable)
        f.setToolTip(path)
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

    def on_failed(self, path, err):
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

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(INK)
        p.setPen(QPen(rgba(CREAM, 22), 1))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 22, 22)

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
