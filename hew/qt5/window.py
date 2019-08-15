from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QSlider, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QPlainTextEdit)

from hew.qt5.mixin import ActivationHandoverMixin, DraggingMixin
from hew.util import format_timedelta, format_timedelta_range, Scheme


scheme = Scheme()


class Window(DraggingMixin, QWidget):
    def __init__(self, player_view, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.player_view = player_view
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.attach_player_view(event.pos())

    def attach_player_view(self, pos):
        if self.player_view is None:
            return
        x = pos.x()
        y = pos.y()
        self.player_view.move(x, y - self.player_view.height())


@scheme
def window(app, player_view, layout, screen):
    window = Window(player_view)
    window.setFixedWidth(640)
    window.setLayout(layout)
    window.show()
    window.activateWindow()
    window.raise_()

    # Center window
    if player_view is None:
        window.move(screen.center() - window.rect().center())
    else:
        setattr(player_view, '_activation_target', window)

        # x: center based on player_view
        # y: center based on both
        center = screen.center() - player_view.rect().center()
        cx, cy = center.x(), center.y() - window.height()/2
        window.move(cx, cy + player_view.height())

    return window


class PlayerView(ActivationHandoverMixin, QWidget):
    pass


@scheme
def player_view(app, video):
    if video is None:
        return None

    player_view = PlayerView()
    player_view.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
    player_view.setFixedSize(*video.size)
    player_view.show()
    player_view.raise_()
    return player_view


@scheme
def layout(app, indicator_layout, slider_layout, clipbox):
    layout = QVBoxLayout()
    layout.addLayout(indicator_layout)
    layout.addLayout(slider_layout)
    layout.addWidget(clipbox)
    return layout


@scheme
def indicator_layout(app,
                     title_label,
                     mark_label,
                     action_label,
                     font_metrics):
    layout = QHBoxLayout()
    layout.setContentsMargins(5, 0, 5, 0)

    left = QVBoxLayout()
    left.addWidget(title_label)
    layout.addLayout(left, stretch=1)

    layout.addSpacing(font_metrics.width('mm'))

    right = QVBoxLayout()
    right.addWidget(action_label, alignment=Qt.AlignLeft)
    right.addWidget(mark_label, alignment=Qt.AlignLeft)
    layout.addLayout(right, stretch=1)

    return layout


@scheme
def title_label(app, title):
    label = QLabel(title)
    return label


@scheme
def action_label(app):
    label = QLabel('-')
    return label


@scheme
def mark_label(app, font_metrics):
    z = format_timedelta_range(left_ms=0, right_ms=0)
    label = QLabel(z)
    width = font_metrics.width(z)
    label.setFixedWidth(width)
    return label


@scheme
def slider_layout(app, time_labels_layout, slider):
    layout = QVBoxLayout()
    layout.addLayout(time_labels_layout)
    layout.addWidget(slider)
    return layout


@scheme
def time_labels_layout(app, current_time_label, duration_time_label):
    layout = QHBoxLayout()
    layout.setContentsMargins(5, 0, 5, 0)
    layout.addWidget(current_time_label)
    layout.addStretch(1)
    layout.addWidget(duration_time_label, alignment=Qt.AlignRight)
    return layout


@scheme
def current_time_label(app, font_metrics):
    z = format_timedelta(0)
    label = QLabel(z)
    width = font_metrics.width(z)
    label.setFixedWidth(width)
    return label


@scheme
def duration_time_label(app, font_metrics, duration):
    z = format_timedelta(duration)
    label = QLabel(z)
    width = font_metrics.width(z)
    label.setFixedWidth(width)
    return label


@scheme
def slider(app, duration, current_time_label, set_position):
    slider = QSlider(Qt.Horizontal)
    slider.setRange(0, duration)
    slider.setValue(0)

    slider.sliderMoved.connect(set_position)

    def update_current_time_label(ms):
        current_time_label.setText(format_timedelta(ms))

    slider.valueChanged.connect(update_current_time_label)

    return slider


@scheme
def clipbox(app, font_metrics):
    text = QPlainTextEdit()
    text.setReadOnly(True)
    # FIXME: Hard coded 8 lines for the height,is there a better way?
    text.setFixedHeight(font_metrics.lineSpacing() * 8)
    return text


@scheme
def tick(app, window, slider, vlc_main):

    def update_slider():
        ms = vlc_main.get_time()
        slider.setValue(ms)

    timer = QTimer(window)
    timer.setInterval(200)
    timer.timeout.connect(update_slider)
    timer.start()
    return timer
