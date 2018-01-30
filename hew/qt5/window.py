from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QSlider, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QTextEdit)

from hew.qt5.mixin import DraggingMixin
from hew.util import format_timedelta, format_timedelta_range, Scheme


scheme = Scheme()


class Window(DraggingMixin, QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)


@scheme
def window(app, screen, layout, player_view):
    window = Window()
    window.setFixedWidth(640)
    window.setLayout(layout)
    window.show()
    window.activateWindow()
    window.raise_()

    # Center window
    if player_view is None:
        window.move(screen.center() - window.rect().center())
    else:
        # x: center based on player_view
        # y: center based on both
        center = screen.center() - player_view.rect().center()
        cx, cy = center.x(), center.y() - window.height()/2
        player_view.move(cx, cy)
        window.move(cx, cy + player_view.height())

    return window


@scheme
def player_view(app, player_default_size):
    if player_default_size is None:
        return None

    window = Window()
    window.setFixedSize(*player_default_size)
    window.show()
    window.raise_()
    return window


@scheme
def layout(app, indicator_layout, slider, clipbox):
    layout = QVBoxLayout()
    layout.addLayout(indicator_layout)
    layout.addWidget(slider)
    layout.addWidget(clipbox)
    return layout


@scheme
def indicator_layout(app,
                     title_label,
                     time_label,
                     mark_label,
                     action_label,
                     font_metrics):
    left = QVBoxLayout()
    left.addWidget(title_label)
    left.addWidget(time_label, alignment=Qt.AlignLeft)

    right = QVBoxLayout()
    right.addWidget(action_label, alignment=Qt.AlignLeft)
    right.addWidget(mark_label, alignment=Qt.AlignLeft)

    layout = QHBoxLayout()
    layout.addLayout(left)
    layout.addSpacing(font_metrics.width('mm'))
    layout.addLayout(right)
    return layout


@scheme
def title_label(app, title):
    label = QLabel(title)
    return label


@scheme
def time_label(app, font_metrics):
    z = format_timedelta(0)
    label = QLabel(z)
    width = font_metrics.width(z)
    label.setFixedWidth(width)
    return label


@scheme
def action_label(app):
    label = QLabel()
    return label


@scheme
def mark_label(app, font_metrics):
    z = format_timedelta_range(left_ms=0, right_ms=0)
    label = QLabel(z)
    width = font_metrics.width(z)
    label.setFixedWidth(width)
    return label


@scheme
def slider(app, duration, time_label, set_position):
    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, duration)
    slider.setValue(0)

    slider.sliderMoved.connect(set_position)

    def update_time_label(ms):
        time_label.setText(format_timedelta(ms))

    slider.valueChanged.connect(update_time_label)

    return slider


@scheme
def clipbox(app, font_metrics):
    text = QTextEdit()
    text.setReadOnly(True)
    # FIXME: Hard coded 5 lines height, is there a better way?
    text.setFixedHeight(font_metrics.lineSpacing() * 5)
    return text


@scheme
def tick(app, window, slider, vlc_main):
    def f():
        ms = vlc_main.get_time()
        slider.setValue(ms)

    timer = QTimer(window)
    timer.setInterval(200)
    timer.timeout.connect(f)
    timer.start()
    return timer
