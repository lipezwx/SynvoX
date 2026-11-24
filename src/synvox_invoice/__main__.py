import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import APP_NAME, ORG_NAME, __version__, paths
from .app import App
from .theme import font


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setApplicationVersion(__version__)
    app.setFont(font(15))
    app.setWindowIcon(QIcon(paths.asset("synvox_icon.png")))
    window = App()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
