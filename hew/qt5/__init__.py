import sys

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QFont, QFontMetrics, QPixmap
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


@scheme
def clip_image(app):
    def f(path):
        cb = app.clipboard()
        pm = QPixmap(path)
        cb.setPixmap(pm)
    return f


@scheme
def font_metrics(app):
    font = QFont()
    return QFontMetrics(font)


@scheme
def settings(app):
    return QSettings('yeonghoey', 'hew')


@scheme
def save_settings(app, settings, window, state):
    def f():
        settings.setValue('geometry', window.saveGeometry())
        settings.setValue('scale', state.get('scale', 1.0))
    return f


@scheme
def restore_settings(app, settings, window, resize):
    g = settings.value('geometry', None)
    if g is not None:
        window.restoreGeometry(g)

    s = settings.value('scale', 1.0, type=float)
    resize(s, absolute=True)
