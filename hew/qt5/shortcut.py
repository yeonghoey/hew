from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from hew.util import Scheme


scheme = Scheme()


@scheme
def shortcut_quit(app, window, quit_):
    k = QKeySequence('Q')
    s = QShortcut(k, window)
    s.activated.connect(quit_)
    return s


@scheme
def shortcut_toggle(app, window, toggle):
    k = QKeySequence(' ')
    s = QShortcut(k, window)
    s.activated.connect(toggle)
    return s


@scheme
def shortcut_seek(app, window, seek):
    def add(ch, ms):
        k = QKeySequence(ch)
        s = QShortcut(k, window)
        s.activated.connect(lambda: seek(ms))
        return s

    return [
        add('J', -2000),
        add('Shift+J', -30000),
        add('l', +2000),
        add('Shift+L', +30000),
    ]


@scheme
def shortcut_mark(app, window, mark, hew):
    left_k = QKeySequence('K')
    left_s = QShortcut(left_k, window)

    def mark_left():
        mark('left')
    left_s.activated.connect(lambda: mark('left'))

    right_k = QKeySequence('Shift+K')
    right_s = QShortcut(right_k, window)

    def mark_right():
        mark('right')
        hew()
    right_s.activated.connect(mark_right)

    return (left_s, right_s)


@scheme
def shortcut_adjust(app, window, mark, adjust):
    def add(ch, side, ms):
        k = QKeySequence(ch)
        s = QShortcut(k, window)
        s.activated.connect(lambda: adjust(side, ms))
        return s

    return [
        add('a', 'left', +100),
        add('z', 'left', -100),
        add('s', 'right', +100),
        add('x', 'right', -100),
    ]


@scheme
def shortcut_hew(app, window, hew):
    k = QKeySequence('C')
    s = QShortcut(k, window)
    s.activated.connect(hew)
    return s


@scheme
def shortcut_dump_sound(app, window, dump_sound):
    k = QKeySequence('D')
    s = QShortcut(k, window)
    s.activated.connect(dump_sound)
    return s


@scheme
def shortcut_dump_srt(app, window, dump_srt):
    k = QKeySequence('Ctrl+D')
    s = QShortcut(k, window)
    s.activated.connect(dump_srt)
    return s


@scheme
def shortcut_dump_recognized(app, window, dump_recognized):
    k = QKeySequence('Ctrl+Shift+D')
    s = QShortcut(k, window)
    s.activated.connect(dump_recognized)
    return s


@scheme
def shortcut_play_hewn(app, window, play_hewn):
    k = QKeySequence('R')
    s = QShortcut(k, window)
    s.activated.connect(play_hewn)
    return s


@scheme
def shortcut_reload(app, window, reload_):
    k = QKeySequence('Shift+R')
    s = QShortcut(k, window)
    s.activated.connect(reload_)
    return s


@scheme
def shortcut_scale(app, window, resize):

    def add(key, ratio, absolute=False):
        k = QKeySequence(key)
        s = QShortcut(k, window)
        s.activated.connect(lambda: resize(ratio, absolute))
        return s

    return [
        add('Ctrl+-', 0.5),
        add('Ctrl+0', 1.0, absolute=True),
        add('Ctrl+=', 2.0),
    ]


@scheme
def shortcut_take_snapshot(app, window, take_snapshot):
    k = QKeySequence('Ctrl+C')
    s = QShortcut(k, window)
    s.activated.connect(take_snapshot)
    return s


@scheme
def shortcut_shift(app, window):
    def shift(dx, dy):
        window.move(window.x() + dx, window.y() + dy)

    def add(key, dx, dy):
        k = QKeySequence(key)
        s = QShortcut(k, window)
        s.activated.connect(lambda: shift(dx, dy))
        return s

    STEP = 16
    return [
        add('Left', -STEP, 0),
        add('Right', +STEP, 0),
        add('Up', 0, -STEP),
        add('Down', 0, +STEP),
    ]


@scheme
def shortcut_cycle_subtitles(app, window, cycle_subtitles):
    k = QKeySequence('Ctrl+S')
    s = QShortcut(k, window)
    s.activated.connect(cycle_subtitles)
    return s


@scheme
def shortcut_yank(app, window, yank):
    k = QKeySequence('Y')
    s = QShortcut(k, window)
    s.activated.connect(yank)
    return s


@scheme
def shortcut_yank_source(app, window, yank_source):
    k = QKeySequence('Shift+Y')
    s = QShortcut(k, window)
    s.activated.connect(yank_source)
    return s
