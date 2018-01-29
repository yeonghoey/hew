import sys

from PyQt5.QtCore import QUrl
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton

from hew.util import Context


ui = Context()


def run(ctx):
    ui.build(ctx)
    sys.exit(ctx['app'].exec_())


@ui
def app():
    # 'hew' uses 'click' to process commandline arguments
    # On top of that, 'hew' use no additional Qt arguments.
    # So, just pass the first argument(the script path) to QApplication
    # SEE: https://doc.qt.io/qt-5/qapplication.html#QApplication
    argv = sys.argv[:1]
    return QApplication(argv)


@ui
def mainwindow(app):
    w = QMainWindow()
    w.setFixedSize(640, 480)
    w.show()
    return w


@ui
def mediaplayer(media, videowidget):
    player = QMediaPlayer()
    player.setVideoOutput(videowidget)
    player.setMedia(media)
    player.play()
    return player


@ui
def media(srcpath):
    return QMediaContent(QUrl.fromLocalFile(srcpath))


@ui
def videowidget():
    w = QVideoWidget()
    w.show()
    return w
