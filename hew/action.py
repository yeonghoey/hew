from datetime import datetime
import os

from hew.util import Scheme


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
def seek(vlc_main, clamp):
    def f(ms):
        t = vlc_main.get_time() + ms
        vlc_main.set_time(clamp(t))
    return f


@scheme
def play(vlc_main):
    def f():
        vlc_main.play()
    return f


@scheme
def reload_and_play(vlc_main, source_path):
    def f():
        ms = vlc_main.get_time()
        vlc_main.set_mrl(source_path)
        vlc_main.play()
        vlc_main.set_time(ms)
    return f


@scheme
def pause(vlc_main):
    def f():
        # NOTE: vlc_main.pause() acts like toggle,
        # but does not act consistently.
        vlc_main.set_pause(1)
    return f


@scheme
def hew(vlc_main,
        vlc_sub,
        anki_media,
        audio,
        state,
        pause):

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
        vlc_sub.set_mrl(filepath)
        vlc_sub.play()
        # Seek to the right end
        vlc_main.set_time(right)

    return f


@scheme
def replay_hewed(vlc_sub, state, pause):
    def f():
        path = state['last_hewed_path']
        if not path:
            return
        vlc_sub.set_mrl(path)
        vlc_sub.play()
    return f


@scheme
def mark(vlc_main, state):
    def f(side):
        assert side == 'left' or side == 'right'
        state[side] = vlc_main.get_time()
    return f


@scheme
def adjust(state, clamp):
    def f(side, ms):
        assert side == 'left' or side == 'right'
        t = state[side] + ms
        state[side] = clamp(t)
    return f


@scheme
def dump(anki_media,
         state,
         use_srt,
         extract_subtitles,
         recognize_hewed,
         clip):

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

    return f


@scheme
def set_position(vlc_main):
    def f(ms):
        vlc_main.set_time(ms)
    return f
