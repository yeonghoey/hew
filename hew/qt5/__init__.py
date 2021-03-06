import pkgutil
import sys

from PyQt5.QtCore import QSettings, QEvent
from PyQt5.QtGui import QFont, QFontMetrics, QPixmap, QIcon, QImage
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
    a = QApplication(argv)

    # NOTE: This is for future use.
    # This doesn't replace the display name "Python" to "hew on macOS
    a.setApplicationName('Hew')

    # Load Icon
    data = pkgutil.get_data('hew', 'hew.png')
    image = QImage.fromData(data)
    pixmap = QPixmap.fromImage(image)
    icon = QIcon(pixmap)
    a.setWindowIcon(icon)
    return a


@scheme
def register_save_when_quit(app, save_settings):
    app.aboutToQuit.connect(save_settings)


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
def save_settings(app, settings, window, main_view, state):
    def f():
        settings.setValue('current_target', state['current_target'])
        settings.setValue('geometry', window.saveGeometry())
        if main_view is not None:
            settings.setValue('scale', state.get('scale', 1.0))
    return f


@scheme
def restore_settings(app, settings, window, main_view, sub_view, resize, set_current_target):
    g = settings.value('geometry', None)
    if g is not None:
        window.restoreGeometry(g)

    current_target = settings.value('current_target', None)
    if current_target is not None:
        set_current_target(current_target)

    if (main_view is not None) and (sub_view is not None):
        s = settings.value('scale', 1.0, type=float)
        resize(s, absolute=True)
