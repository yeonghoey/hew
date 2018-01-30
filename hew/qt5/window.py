from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QSlider, QHBoxLayout, QVBoxLayout, QWidget, QLabel

from hew.qt5.mixin import DraggingMixin
from hew.util import format_timedelta, format_timedelta_range, Scheme


scheme = Scheme()


class Window(DraggingMixin, QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)


@scheme
def window(app, screen, layout, player_view):
    w = Window()
    w.setFixedWidth(640)
    w.setLayout(layout)
    w.show()
    w.activateWindow()
    w.raise_()

    # Center window
    if player_view is None:
        w.move(screen.center() - w.rect().center())
    else:
        # Center player_view, put window below it.
        player_view.move(screen.center() - player_view.rect().center())
        w.move(player_view.x(), player_view.y() + player_view.height())

    return w


@scheme
def player_view(app, player_default_size):
    if player_default_size is None:
        return None

    w = Window()
    w.setFixedSize(*player_default_size)
    w.show()
    w.raise_()
    return w


@scheme
def layout(app, indicator_layout, slider):
    box = QVBoxLayout()
    box.addLayout(indicator_layout)
    box.addWidget(slider)
    return box


@scheme
def indicator_layout(app,
                     title_label,
                     time_label,
                     mark_label,
                     action_label,
                     str_width):
    left = QVBoxLayout()
    left.addWidget(title_label)
    left.addWidget(time_label, alignment=Qt.AlignLeft)

    right = QVBoxLayout()
    right.addWidget(action_label, alignment=Qt.AlignLeft)
    right.addWidget(mark_label, alignment=Qt.AlignLeft)

    box = QHBoxLayout()
    box.addLayout(left)
    box.addSpacing(str_width('mm'))
    box.addLayout(right)
    return box


@scheme
def title_label(app, title):
    w = QLabel(title)
    return w


@scheme
def time_label(app, str_width):
    z = format_timedelta(0)
    w = QLabel(z)
    width = str_width(z)
    w.setFixedWidth(width)
    return w


@scheme
def action_label(app):
    w = QLabel()
    return w


@scheme
def mark_label(app, str_width):
    z = format_timedelta_range(left_ms=0, right_ms=0)
    w = QLabel(z)
    width = str_width(z)
    w.setFixedWidth(width)
    return w


@scheme
def slider(app, duration, time_label, set_position):
    s = QSlider(Qt.Horizontal)
    s.setRange(0, duration)
    s.setValue(0)

    s.sliderMoved.connect(set_position)

    def update_display(ms):
        time_label.setText(format_timedelta(ms))

    s.valueChanged.connect(update_display)

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
