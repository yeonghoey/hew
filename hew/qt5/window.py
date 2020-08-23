from PyQt5.QtCore import QEvent, Qt, QTimer
from PyQt5.QtWidgets import (
    QSlider, QHBoxLayout, QVBoxLayout, QWidget, QLabel, QPlainTextEdit, QStyle)

from hew.qt5.mixin import ActivationHandoverMixin, DraggingMixin
from hew.util import format_timedelta, format_timedelta_range, Scheme


scheme = Scheme()

# Window is for keeping the layout as below.
# +----------------------+
# |                      |
# |  main_view[sub_view] |
# |                      |
# +---------+------------+
# | window  |
# +---------+


class Window(DraggingMixin, QWidget):
    def __init__(self, main_view, sub_view, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_view = main_view
        self.sub_view = sub_view
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

    def event(self, e):
        if e.type() == QEvent.WindowActivate:
            if self.main_view is not None:
                self.main_view.raise_()
            if self.sub_view is not None:
                self.sub_view.raise_()
            self.raise_()
        return super().event(e)

    def moveEvent(self, event):
        super().moveEvent(event)
        self.sync_view_positions(event.pos())

    def sync_view_positions(self, pos):
        self._attach_main_view(pos)
        self._attach_sub_view(pos)

    def _attach_main_view(self, pos):
        if self.main_view is None:
            return
        x = pos.x()
        y = pos.y()
        self.main_view.move(x, y - self.main_view.height())

    def _attach_sub_view(self, pos):
        if self.sub_view is None:
            return
        x = pos.x()
        y = pos.y()
        self.sub_view.move(x, y - self.sub_view.height())


@scheme
def window(app, main_view, sub_view, layout, screen):
    window = Window(main_view, sub_view)
    window.setFixedWidth(960)
    window.setFixedHeight(200)
    window.setLayout(layout)
    window.show()
    window.activateWindow()
    window.raise_()

    if main_view is not None:
        setattr(main_view, '_activation_target', window)
    if sub_view is not None:
        setattr(sub_view, '_activation_target', window)

    # Move the window and views on the default position.
    # x: center based on main_view
    # y: center based on both
    if main_view is not None:
        center = screen.center() - main_view.rect().center()
        cx, cy = center.x(), center.y() - window.height()/2
        window.move(cx, cy + main_view.height())
    else:
        window.move(screen.center() - window.rect().center())
    return window


class PlayerView(ActivationHandoverMixin, QWidget):
    pass


@scheme
def main_view(app, video):
    if video is None:
        return None

    player_view = PlayerView()
    player_view.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
    # NOTE: View size will be updated by resize()
    player_view.show()
    player_view.raise_()
    return player_view


@scheme
def sub_view(app, video):
    if video is None:
        return None

    player_view = PlayerView()
    player_view.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
    # NOTE: View size will be updated by resize().
    # Calling show() even though it will be hidden initially,
    # because QWidget should be shown before any other positioning operations.
    # SEE: https://www.qtcentre.org/threads/5151-Need-to-know-widget-size-before-first-shown
    player_view.show()
    player_view.hide()
    return player_view


@scheme
def layout(app, indicator_layout, slider_layout, clipbox):
    layout = QVBoxLayout()
    layout.addStretch(1)
    layout.addLayout(indicator_layout)
    layout.addStretch(1)
    layout.addLayout(slider_layout)
    layout.addStretch(1)
    layout.addWidget(clipbox)
    layout.addStretch(1)
    return layout


@scheme
def indicator_layout(app,
                     title_label,
                     subtitles_pri_label,
                     subtitles_aux_label,
                     mark_label,
                     current_player_label,
                     current_target_label,
                     try_video_label,
                     action_label,
                     font_metrics):
    layout = QHBoxLayout()
    layout.setContentsMargins(5, 0, 5, 0)

    left = QVBoxLayout()
    left.addWidget(title_label)
    lbottom = QHBoxLayout()
    lbottom.addWidget(subtitles_pri_label)
    lbottom.addWidget(subtitles_aux_label)
    lbottom.addStretch(1)
    left.addLayout(lbottom)
    layout.addLayout(left, stretch=2)

    layout.addSpacing(font_metrics.width('mm'))

    mid = QVBoxLayout()
    mid.addWidget(action_label, alignment=Qt.AlignLeft)
    mid.addWidget(mark_label, alignment=Qt.AlignLeft)
    layout.addLayout(mid, stretch=2)

    layout.addSpacing(font_metrics.width('mm'))

    right = QVBoxLayout()
    right.addWidget(current_player_label, alignment=Qt.AlignRight)
    rbottom = QHBoxLayout()
    rbottom.addStretch(1)
    rbottom.addWidget(current_target_label)
    rbottom.addWidget(try_video_label)
    right.addLayout(rbottom)
    layout.addLayout(right, stretch=1)

    return layout


@scheme
def title_label(app, title):
    label = QLabel(title)
    return label


@scheme
def subtitles_pri_label(app):
    label = QLabel()
    return label


@scheme
def subtitles_aux_label(app):
    label = QLabel()
    return label


@scheme
def update_subtitles_pri_label(subtitles_pri_label, subtitles_pri_map, label_style_color, state):
    def f():
        update_subtitles_label(subtitles_pri_label,
                               subtitles_pri_map, label_style_color)
    return f


@scheme
def update_subtitles_aux_label(subtitles_aux_label, subtitles_aux_map, label_style_color, state):
    def f():
        update_subtitles_label(subtitles_aux_label,
                               subtitles_aux_map, label_style_color)

    return f


def update_subtitles_label(label, smap, color):
    _, spec = smap.current()
    name, _ = spec
    label.setText(name)
    if smap.enabled:
        color(label, 'black')
    else:
        color(label, 'lightgray')


@scheme
def action_label(app):
    label = QLabel('-')
    return label


@scheme
def mark_label(app, font_metrics):
    label = QLabel()
    return label


@scheme
def current_player_label(app, state):
    t = state['current_player']
    label = QLabel(t)
    return label


@scheme
def current_target_label(app, state):
    t = state['current_target']
    label = QLabel(t)
    return label


@scheme
def try_video_label(app, state, try_video_label_text):
    t = try_video_label_text(state['try_video'])
    label = QLabel(t)
    return label


@scheme
def try_video_label_text():
    def f(try_video):
        # NOTE: hewn files can only be either mp4 or mp3.
        return 'mp4' if try_video else 'mp3'
    return f


@scheme
def slider_layout(app, time_labels_layout, slider):
    layout = QVBoxLayout()
    layout.addStretch(1)
    layout.addLayout(time_labels_layout)
    layout.addWidget(slider)
    layout.addStretch(1)
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
def label_style_normal(app):
    def f(label):
        label.setStyleSheet(
            'QLabel { color: black; background-color : transparent; }')
    return f


@scheme
def label_style_color(app):
    def f(label, color, bg_color='transparent'):
        label.setStyleSheet(
            f'QLabel {{color: {color}; background-color: {bg_color}; }}')
    return f


@scheme
def label_style_notice(app):
    def f(label):
        label.setStyleSheet(
            "QLabel { color: black; background-color : yellow; }")
    return f


@scheme
def clipbox(app, font_metrics):
    text = QPlainTextEdit()
    text.setReadOnly(True)
    text.setFixedHeight(font_metrics.lineSpacing() * 2)
    return text


@scheme
def tick(app, window, slider, main_vlc):

    def update_slider():
        ms = main_vlc.get_time()
        slider.setValue(ms)

    timer = QTimer(window)
    timer.setInterval(200)
    timer.timeout.connect(update_slider)
    timer.start()
    return timer
