"""Where the app reads assets from and writes user data to."""
import os
import sys


def resource_dir():
    """Folder holding bundled assets (works from source and from a PyInstaller build)."""
    if getattr(sys, "frozen", False):
        return os.path.join(getattr(sys, "_MEIPASS", os.path.dirname(sys.executable)),
                            "synvox_invoice", "assets")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def asset(name):
    return os.path.join(resource_dir(), name)


def data_dir():
    """Per-user writable folder (an installed app must not write into Program Files)."""
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    path = os.path.join(base, "Synvox", "InvoiceExtractor")
    os.makedirs(path, exist_ok=True)
    return path


def logs_dir():
    return os.path.join(data_dir(), "logs")


def default_export_path():
    docs = os.path.join(os.path.expanduser("~"), "Documents")
    folder = docs if os.path.isdir(docs) else os.path.expanduser("~")
    return os.path.join(folder, "Contas_a_Pagar.xlsx")
