"""
OCR for scanned or image-only PDFs. No GUI code here.

Engines (chosen automatically, best first):
  1. Tesseract with the Portuguese model, if the `tesseract` binary is found
     (PATH, SYNVOX_TESSERACT, a bundled copy, or the usual Windows install folders).
  2. RapidOCR (PaddleOCR models on ONNX Runtime). Pure pip, offline, ships with the installer.
  3. Tesseract without Portuguese (English model only).

Force one with the SYNVOX_OCR_ENGINE environment variable: tesseract | rapidocr | auto (default).
Disable OCR completely with SYNVOX_OCR=0.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading

RENDER_DPI = 300

_lock = threading.Lock()
_engine = None
_engine_checked = False


def enabled():
    return os.environ.get("SYNVOX_OCR", "1").strip().lower() not in ("0", "false", "no", "off")


# ---------------------------------------------------------------
# Page rendering (PDF -> PIL images)
# ---------------------------------------------------------------
def render_pages(path, page_indexes, dpi=RENDER_DPI):
    """Render the given 0-based pages. Uses pypdfium2, falling back to PyMuPDF."""
    images = []
    try:
        import pypdfium2 as pdfium
        pdf = pdfium.PdfDocument(path)
        try:
            for i in page_indexes:
                if i < len(pdf):
                    images.append(pdf[i].render(scale=dpi / 72).to_pil().convert("RGB"))
        finally:
            pdf.close()
        return images
    except ImportError:
        pass
    import fitz                                    # PyMuPDF
    from PIL import Image
    with fitz.open(path) as doc:
        for i in page_indexes:
            if i < len(doc):
                pix = doc[i].get_pixmap(dpi=dpi)
                images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
    return images


# ---------------------------------------------------------------
# Engines
# ---------------------------------------------------------------
class TesseractEngine:
    def __init__(self, binary, lang):
        self.binary, self.lang = binary, lang
        self.name = f"Tesseract ({lang})"
        self.good = "por" in lang

    @staticmethod
    def find_binary():
        env = os.environ.get("SYNVOX_TESSERACT")
        if env and os.path.isfile(env):
            return env
        try:                                       # a copy bundled inside the installer
            from . import paths
            bundled = os.path.join(paths.resource_dir(), "..", "tesseract",
                                   "tesseract.exe" if os.name == "nt" else "tesseract")
            if os.path.isfile(bundled):
                return os.path.abspath(bundled)
        except Exception:
            pass
        found = shutil.which("tesseract")
        if found:
            return found
        if os.name == "nt":
            for base in (os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"),
                         os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs")):
                if base:
                    cand = os.path.join(base, "Tesseract-OCR", "tesseract.exe")
                    if os.path.isfile(cand):
                        return cand
        return None

    @classmethod
    def create(cls):
        binary = cls.find_binary()
        if not binary:
            return None
        try:
            out = subprocess.run([binary, "--list-langs"], capture_output=True, text=True,
                                 timeout=20, creationflags=_NO_WINDOW).stdout
        except Exception:
            return None
        langs = {l.strip() for l in out.splitlines()[1:] if l.strip()}
        if "por" in langs:
            lang = "por+eng" if "eng" in langs else "por"
        elif "eng" in langs:
            lang = "eng"
        else:
            return None
        return cls(binary, lang)

    def recognize(self, image):
        with tempfile.TemporaryDirectory() as tmp:
            png = os.path.join(tmp, "page.png")
            image.save(png)
            res = subprocess.run(
                [self.binary, png, "stdout", "-l", self.lang, "--psm", "6", "--dpi", str(RENDER_DPI),
                 "-c", "preserve_interword_spaces=1"],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=180, creationflags=_NO_WINDOW)
        if res.returncode != 0:
            raise RuntimeError(f"Tesseract failed: {res.stderr.strip()[:200]}")
        return res.stdout


class RapidOcrEngine:
    name = "RapidOCR"
    good = True

    def __init__(self, ocr):
        self._ocr = ocr

    @classmethod
    def create(cls):
        try:
            from rapidocr_onnxruntime import RapidOCR
            return cls(RapidOCR())
        except Exception:
            return None

    def recognize(self, image):
        import numpy as np
        result, _ = self._ocr(np.array(image.convert("RGB"))[:, :, ::-1])   # RGB -> BGR for OpenCV
        return boxes_to_text(result or [])


def boxes_to_text(result):
    """Turn [(box, text, score), ...] into text lines in reading order.
    Boxes whose vertical centres are close belong to the same line; words are joined by two spaces."""
    items = []
    for box, text, *_ in result:
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append(((min(ys) + max(ys)) / 2, max(ys) - min(ys), min(xs), text))
    if not items:
        return ""
    heights = sorted(h for _, h, _, _ in items)
    tol = max(4.0, heights[len(heights) // 2] * 0.6)
    items.sort(key=lambda t: t[0])
    lines, cur, cur_y = [], [], None
    for cy, _, x, text in items:
        if cur and abs(cy - cur_y) > tol:
            lines.append(cur)
            cur = []
        cur.append((x, text))
        cur_y = cy if len(cur) == 1 else (cur_y * (len(cur) - 1) + cy) / len(cur)
    if cur:
        lines.append(cur)
    return "\n".join("  ".join(t for _, t in sorted(line)) for line in lines)


_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0


def get_engine():
    """The best available engine, or None. Cached after the first call."""
    global _engine, _engine_checked
    with _lock:
        if _engine_checked:
            return _engine
        pref = os.environ.get("SYNVOX_OCR_ENGINE", "auto").strip().lower()
        tess = None
        candidates = []
        if pref in ("auto", "tesseract"):
            tess = TesseractEngine.create()
            if tess and (tess.good or pref == "tesseract"):
                candidates.append(tess)
        if pref in ("auto", "rapidocr"):
            rap = RapidOcrEngine.create()
            if rap:
                candidates.append(rap)
        if pref == "auto" and tess and not tess.good:
            candidates.append(tess)
        _engine = candidates[0] if candidates else None
        _engine_checked = True
        return _engine


def reset_engine():
    """Forget the cached engine (used by tests)."""
    global _engine, _engine_checked
    with _lock:
        _engine, _engine_checked = None, False


# ---------------------------------------------------------------
# Public API
# ---------------------------------------------------------------
def ocr_pdf_pages(path, page_indexes):
    """OCR the given pages. Returns {page_index: text}. Raises RuntimeError if no engine exists."""
    engine = get_engine()
    if engine is None:
        raise RuntimeError("No OCR engine available. Install RapidOCR (pip install rapidocr-onnxruntime) "
                           "or Tesseract with the Portuguese language pack.")
    out = {}
    for i, img in zip(page_indexes, render_pages(path, page_indexes)):
        out[i] = engine.recognize(img)
    return out


# Characters OCR engines confuse with digits. Used only inside tokens that are mostly digits.
_DIGIT_LOOKALIKES = str.maketrans({"O": "0", "o": "0", "D": "0", "Q": "0", "l": "1", "I": "1", "|": "1",
                                   "i": "1", "S": "5", "s": "5", "B": "8", "Z": "2", "z": "2"})


def normalize_ocr_text(text):
    """Fix the classic OCR slips inside number-like tokens (O->0, l->1, S->5 ...).
    A token is only touched when it is at least 6 characters long and at least 70% digits,
    so ordinary words are never altered."""
    def fix(tok):
        digits = sum(c.isdigit() for c in tok)
        core = re.sub(r"[.\-/,]", "", tok)
        if len(core) >= 6 and digits / max(1, len(core)) >= 0.7:
            return tok.translate(_DIGIT_LOOKALIKES)
        return tok
    return re.sub(r"[^\s]+", lambda m: fix(m.group(0)), text)
