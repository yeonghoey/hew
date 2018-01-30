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
def shortcut_dump(app, window, dump):
    soundonly_k = QKeySequence('D')
    soundonly_s = QShortcut(soundonly_k, window)
    soundonly_s.activated.connect(lambda: dump(do_transcript=False))

    transcript_k = QKeySequence('Shift+D')
    transcript_s = QShortcut(transcript_k, window)
    transcript_s.activated.connect(lambda: dump(do_transcript=True))
    return [soundonly_s, transcript_s]


@scheme
def shortcut_play_hewed(app, window, play_hewed):
    k = QKeySequence('R')
    s = QShortcut(k, window)
    s.activated.connect(play_hewed)
    return s


@scheme
def shortcut_reload(app, window, reload_):
    k = QKeySequence('Shift+R')
    s = QShortcut(k, window)
    s.activated.connect(reload_)
    return s
