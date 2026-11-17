# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: one-folder, windowed build of Synvox Invoice Extractor.
#   pyinstaller installer/synvox.spec --noconfirm
import os

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "synvox_invoice", "assets")

# OCR: RapidOCR ships its ONNX models and config as data files; ONNX Runtime and pdfium ship native libs
ocr_datas, ocr_bins, ocr_hidden = [], [], []
for pkg in ("rapidocr_onnxruntime", "onnxruntime", "pypdfium2", "pypdfium2_raw"):
    try:
        d, b, h = collect_all(pkg)
        ocr_datas += d
        ocr_bins += b
        ocr_hidden += h
    except Exception:
        pass

a = Analysis(
    [os.path.join(SRC, "synvox_invoice", "__main__.py")],
    pathex=[SRC],
    binaries=ocr_bins,
    datas=[(ASSETS, os.path.join("synvox_invoice", "assets"))] + ocr_datas,
    hiddenimports=["pypdf", "openpyxl", "fitz", "PIL"] + ocr_hidden,
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
              "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtMultimedia"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SynvoxInvoiceExtractor",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon=os.path.join(ASSETS, "synvox_icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="SynvoxInvoiceExtractor",
)
