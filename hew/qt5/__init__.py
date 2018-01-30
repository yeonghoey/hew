import sys

from PyQt5.QtWidgets import QApplication

from hew.qt5 import window, shortcut
from hew.util import Scheme


scheme = Scheme(window.scheme,
                shortcut.scheme)


@scheme
def app():
    # 'hew' uses 'click' to process commandline arguments
    # On top of that, 'hew' use no additional Qt arguments.
    # So, just pass the first argument(the script path) to QApplication
    # SEE: https://doc.qt.io/qt-5/qapplication.html#QApplication
    argv = sys.argv[:1]
    return QApplication(argv)


@scheme
def screen(app):
    return app.desktop().screenGeometry()
