from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QShortcut

from hew.util import Scheme


scheme = Scheme()


@scheme
def all_shortcut_keys():
    # NOTE: For validating whether or not there are duplicate shortcut definitions.
    # Since the elements can be either a string or a StandardKey, which is unhashable,
    # use list instead of set.
    return []


@scheme
def shortcut(all_shortcut_keys, window, ):
    def f(keys, slot):
        # NOTE: Check if there is a already shortcut for the same key
        assert all(key not in all_shortcut_keys for key in keys)
        all_shortcut_keys.extend(keys)

        shortcuts = [QShortcut(QKeySequence(key), window)
                     for key in keys]
        for s in shortcuts:
            s.activated.connect(slot)
        return shortcuts
    return f


@scheme
def shortcut_toggle(shortcut, toggle):
    return shortcut([' '], toggle)


@scheme
def shortcut_set_main(shortcut, set_current_player):
    return shortcut(['Escape'],
                    lambda: set_current_player('main'))


@scheme
def shortcut_seek(shortcut, seek):
    def add(keys, ms):
        return shortcut(keys, lambda: seek(ms))
    return [
        add(['j', 'ㅓ'], -2000),
        add(['l', 'ㅣ'], +2000),
        add(['Shift+j', 'Shift+ㅓ'], -30000),
        add(['Shift+l', 'Shift+ㅣ'], +30000),
    ]


@scheme
def shortcut_mark(shortcut, mark, hew):
    def mark_left():
        mark('left')

    def mark_right():
        mark('right')
        hew()

    return (
        shortcut(['k', 'ㅏ'], mark_left),
        shortcut(['Shift+k', 'Shift+ㅏ'], mark_right)
    )


@scheme
def shortcut_adjust(shortcut, mark, adjust):
    def add(keys, side, ms):
        return shortcut(keys, lambda: adjust(side, ms))

    return [
        add(['a', 'ㅁ'], 'left', +100),
        add(['z', 'ㅋ'], 'left', -100),
        add(['s', 'ㄴ'], 'right', +100),
        add(['x', 'ㅌ'], 'right', -100),
    ]


@scheme
def shortcut_hew(shortcut, hew):
    return shortcut(['c', 'ㅊ'], hew)


@scheme
def shortcut_dump_primary(shortcut, dump_primary):
    return shortcut(['d', 'ㅇ'], dump_primary)


@scheme
def shortcut_dump_secondary(shortcut, dump_secondary):
    return shortcut(['Shift+d', 'Shift+ㅇ'], dump_secondary)


@scheme
def shortcut_play_hewn_left(shortcut, play_hewn):
    return shortcut(['r', 'ㄱ'],
                    lambda: play_hewn('left'))


@scheme
def shortcut_play_hewn_right(shortcut, play_hewn):
    return shortcut(['Shift+r', 'Shift+ㄱ'],
                    lambda: play_hewn('right'))


@scheme
def shortcut_reload(shortcut, reload_):
    return shortcut([QKeySequence.Refresh], reload_)


@scheme
def shortcut_scale(shortcut, resize):

    def add(keys, ratio, absolute=False):
        return shortcut(keys, lambda: resize(ratio, absolute))

    return [
        add([QKeySequence.ZoomOut], 0.5),
        add(['Ctrl+0'], 1.0, absolute=True),
        add([QKeySequence.ZoomIn], 2.0),
    ]


@scheme
def shortcut_take_snapshot(shortcut, take_snapshot):
    return shortcut([QKeySequence.Print], take_snapshot)


@scheme
def shortcut_shift(shortcut, window):
    def shift(dx, dy):
        window.move(window.x() + dx, window.y() + dy)

    def add(keys, dx, dy):
        return shortcut(keys, lambda: shift(dx, dy))

    STEP = 16
    return [
        add(['Left'], -STEP, 0),
        add(['Right'], +STEP, 0),
        add(['Up'], 0, -STEP),
        add(['Down'], 0, +STEP),
    ]


@scheme
def shortcut_toggle_try_video(shortcut, video, state, try_video_label, try_video_label_text):
    def f():
        try_video = (video is not None) and (not state['try_video'])
        try_video_label.setText(try_video_label_text(try_video))
        state['try_video'] = try_video

    return shortcut(['~'], f)


@scheme
def shortcut_toggle_current_target(shortcut, toggle_current_target):
    return shortcut(['Tab'], toggle_current_target)


@scheme
def shortcut_cycle_subtitles(shortcut, cycle_subtitles):
    return shortcut(['`', '₩'], cycle_subtitles)


@scheme
def shortcut_return_before_bookmark(shortcut, return_before_bookmark):
    return shortcut(['\\'], return_before_bookmark)


@scheme
def shortcut_prev_bookmark(shortcut, prev_bookmark):
    return shortcut(['['], prev_bookmark)


@scheme
def shortcut_next_bookmark(shortcut, next_bookmark):
    return shortcut([']'], next_bookmark)


@scheme
def shortcut_yank(shortcut, yank):
    return shortcut(['y', 'ㅛ'], yank)


@scheme
def shortcut_yank_source(shortcut, yank_source):
    return shortcut(['Shift+y', 'Shift+ㅛ'], yank_source)
