# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: one-folder, windowed build of Synvox Invoice Extractor.
#   pyinstaller installer/synvox.spec --noconfirm
import os

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "synvox_invoice", "assets")

a = Analysis(
    [os.path.join(SRC, "synvox_invoice", "__main__.py")],
    pathex=[SRC],
    binaries=[],
    datas=[(ASSETS, os.path.join("synvox_invoice", "assets"))],
    hiddenimports=["pypdf", "openpyxl", "fitz"],
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
