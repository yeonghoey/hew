from datetime import datetime
import os

import pyperclip

from hew.util import format_timedelta, format_timedelta_range, Scheme


scheme = Scheme()


@scheme
def quit_(app):
    def f():
        app.exit()
    return f


@scheme
def toggle(vlc_main, vlc_sub, play, pause):
    def f():
        if vlc_main.is_playing():
            pause()
        else:
            if vlc_sub.is_playing():
                vlc_sub.stop()
            play()
    return f


@scheme
def play(vlc_main, show_action):
    def f():
        vlc_main.play()
        show_action('play')

    return f


@scheme
def pause(vlc_main, show_action):
    def f():
        # NOTE: vlc_main.pause() acts like toggle,
        # but does not act consistently.
        vlc_main.set_pause(1)
        show_action('pause')
    return f


@scheme
def seek(vlc_main, clamp, show_action):
    def f(ms):
        t = vlc_main.get_time() + ms
        vlc_main.set_time(clamp(t))
        show_action('%+ds' % (ms/1000))
    return f


@scheme
def mark(vlc_main, state, show_action, update_mark):
    def f(side):
        assert side == 'left' or side == 'right'
        state[side] = vlc_main.get_time()
        td = format_timedelta(state[side])
        show_action('%s %s' % (side, td))
        update_mark(state['left'], state['right'])
    return f


@scheme
def adjust(state, clamp, show_action):
    def f(side, ms):
        assert side == 'left' or side == 'right'
        t = state[side] + ms
        state[side] = clamp(t)
        show_action('%s %+dms' % (side, ms))
    return f


@scheme
def hew(vlc_main,
        vlc_sub,
        anki_media,
        audio,
        state,
        pause,
        play_hewed):

    def f():
        left = state['left']
        right = state['right']
        if left >= right:
            return

        pause()
        hewed = audio.subclip(left/1000., right/1000.)
        now = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = now + '.mp3'
        filepath = os.path.join(anki_media, filename)
        hewed.write_audiofile(filepath, verbose=False, progress_bar=False)
        state['last_hewed_path'] = filepath
        state['last_left'] = left
        state['last_right'] = right

        play_hewed()

        # Seek to the right end
        vlc_main.set_time(right)

    return f


@scheme
def play_hewed(vlc_sub, state, pause, show_action):
    def f():
        path = state['last_hewed_path']
        left = state['left']
        right = state['right']
        if not path:
            return

        pause()
        vlc_sub.set_mrl(path)
        vlc_sub.play()

        filename = os.path.basename(path)
        hewed_duration = format_timedelta(right - left)
        show_action('%s (%s)' % (filename, hewed_duration))
    return f


@scheme
def dump(anki_media,
         state,
         use_srt,
         extract_subtitles,
         recognize_hewed,
         clip,
         show_action):

    def f(do_transcript):
        path = state['last_hewed_path']
        if not path:
            return

        left = state['left']
        right = state['right']

        filename = os.path.relpath(path, anki_media)

        sound_str = '[sound:%s]' % filename
        if do_transcript:
            transcript = (extract_subtitles(left, right) if use_srt else
                          recognize_hewed(path))
            text = '%s\n%s' % (sound_str, transcript.strip())
            clip(text)
        else:
            clip(sound_str)
        show_action('dump')

    return f


@scheme
def clip(clipbox):
    def f(s):
        pyperclip.copy(s)
        clipbox.setText(s)
    return f


@scheme
def reload_(vlc_main, source_path, show_action):
    def f():
        ms = vlc_main.get_time()
        vlc_main.set_mrl(source_path)
        vlc_main.play()
        vlc_main.set_time(ms)
        show_action('reload')
    return f


@scheme
def set_position(vlc_main):
    def f(ms):
        vlc_main.set_time(ms)
    return f


@scheme
def show_action(action_label):
    def f(s):
        action_label.setText(s)
    return f


@scheme
def update_mark(mark_label):
    def f(l, r):
        s = format_timedelta_range(l, r)
        mark_label.setText(s)
    return f
