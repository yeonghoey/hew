from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QSlider, QVBoxLayout, QWidget

from hew.qt5.mixin import DraggingMixin
from hew.util import Scheme


scheme = Scheme()


class Window(DraggingMixin, QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)


@scheme
def window(app, layout, screen, player):
    w = Window()
    w.setLayout(layout)
    w.show()
    w.activateWindow()
    w.raise_()

    # Center window
    if player is None:
        w.move(screen.center() - w.rect().center())
    else:
        # Center player, put window below it.
        player.move(screen.center() - player.rect().center())
        w.move(player.x(), player.y() + player.height())

    return w


@scheme
def player(app, player_default_size):
    if player_default_size is None:
        return None

    w = Window()
    w.setFixedSize(*player_default_size)
    w.show()
    w.raise_()
    return w


@scheme
def layout(app, slider):
    vbox = QVBoxLayout()
    vbox.addWidget(slider)
    return vbox


@scheme
def slider(app, duration, set_position):
    s = QSlider(Qt.Horizontal)
    s.setRange(0, duration)
    s.setValue(0)
    s.sliderMoved.connect(set_position)
    return s


@scheme
def tick(app, window, slider, vlc_main):
    def f():
        ms = vlc_main.get_time()
        slider.setValue(ms)

    t = QTimer(window)
    t.setInterval(200)
    t.timeout.connect(f)
    t.start()
