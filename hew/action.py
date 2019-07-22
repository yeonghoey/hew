from datetime import datetime
import os

import pyperclip

from hew.util import (
    format_timedelta, format_timedelta_range, remove_tags, Scheme,
    tempfile_path)


scheme = Scheme()


@scheme
def quit_(app, save_settings):
    def f():
        save_settings()
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
        # NOTE: Ensure that newly marked hewn to be played at start(left).
        state['last_hewn_side'] = 'left'
        state[side] = vlc_main.get_time()
        show_action('%s' % side)
        update_mark(state['left'], state['right'])
    return f


@scheme
def adjust(state, clamp, show_action, update_mark):
    def f(side, ms):
        assert side == 'left' or side == 'right'
        t = state[side] + ms
        # NOTE: Adjusting means that the user cares that side.
        # So keep this state to play on that side after hewing
        state['last_hewn_side'] = side
        state[side] = clamp(t)
        show_action('%s %+dms' % (side, ms))
        update_mark(state['left'], state['right'])
    return f


@scheme
def hew(vlc_main,
        vlc_sub,
        anki,
        anki_media,
        video_no_sound,
        video_no_resize,
        player_view,
        video,
        audio,
        state,
        pause,
        dump_media,
        play_hewn):

    dirname = anki_media if anki else '.'

    def f(try_video):
        left = state['left']
        right = state['right']
        if left >= right:
            return

        pause()

        now = datetime.now().strftime('%Y%m%d-%H%M%S')

        if try_video and video is not None:
            hewn = video.subclip(left/1000., right/1000.)
            filename = now + '.mp4'
            filepath = os.path.join(dirname, filename)

            ffmpeg_params = []
            if not video_no_resize:
                w, h = player_view.width(), player_view.height()
                ffmpeg_params.extend(['-vf', 'scale=%s:%s' % (w, h)])
            # Codecs chosen for HTML5
            hewn.write_videofile(filepath,
                                 codec='libx264',
                                 audio=not video_no_sound,
                                 audio_codec='aac',
                                 ffmpeg_params=ffmpeg_params,
                                 verbose=False,
                                 progress_bar=False)
            dump_media(filename)
        else:
            hewn = audio.subclip(left/1000., right/1000.)
            filename = now + '.mp3'
            filepath = os.path.join(dirname, filename)
            hewn.write_audiofile(filepath, verbose=False, progress_bar=False)
            dump_media(filename)

        state['last_hewn_path'] = filepath
        state['last_left'] = left
        state['last_right'] = right
        play_hewn()

        # Seek to the right end
        vlc_main.set_time(right)

    return f


@scheme
def dump_media(clip, show_action):
    def f(filename):
        sound_str = '[sound:%s]' % filename
        clip(sound_str)
        show_action('dump-sound')

    return f


@scheme
def dump_srt(state,
             subtitles,
             srt_padding,
             clip,
             show_action):

    def f():
        if not subtitles:
            return

        path = state['last_hewn_path']

        if not path:
            return

        left = state['left']
        right = state['right']
        ss = subtitles.slice(starts_after=left - srt_padding,
                             ends_before=right + srt_padding)
        transcript = ' '.join(remove_tags(s.text) for s in ss)
        clip(transcript.strip())
        show_action('dump-srt')

    return f


@scheme
def dump_recognized(state,
                    recognize_hewn,
                    clip,
                    show_action):

    def f():
        path = state['last_hewn_path']
        if not path:
            return

        transcript = recognize_hewn(path)
        clip(transcript.strip())
        show_action('dump-recognized')
    return f


@scheme
def play_hewn(vlc_sub, state, pause, show_action, right_duration):
    def f(side=None):
        path = state['last_hewn_path']
        side = state['last_hewn_side'] if side is None else side
        left = state['left']
        right = state['right']
        if not path:
            return

        pause()
        vlc_sub.set_mrl(path)
        vlc_sub.play()

        duration = right - left
        if side == 'right' and duration != 0:
            # NOTE: For some reason, set_time() doesn't work properly,
            # while set_position() works as expected
            pos = max(0, duration - right_duration) / duration
            vlc_sub.set_position(pos)

        filename = os.path.basename(path)
        hewn_duration = format_timedelta(duration)
        show_action('%s (%s)' % (filename, hewn_duration))
    return f


@scheme
def clip(clipbox):
    def f(s):
        pyperclip.copy(s)
        clipbox.setPlainText(s)
    return f


@scheme
def take_snapshot(vlc_main,
                  player_view,
                  snapshot_dir,
                  clip_image,
                  show_action):

    def f():
        if player_view is None:
            return
        path = tempfile_path('.png', snapshot_dir)
        w = player_view.width()
        h = player_view.height()
        vlc_main.video_take_snapshot(0, path, w, h)
        clip_image(path)
        show_action('take-screenshot')
    return f


@scheme
def reload_(vlc_main, main_path, show_action):
    def f():
        ms = vlc_main.get_time()
        vlc_main.set_mrl(main_path)
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


@scheme
def resize(screen, window, player_view, video, state):
    def f(x, absolute=False):
        if player_view is None:
            return

        if absolute:
            scale = x
        else:
            scale = state['scale'] * x

        w, h = video.size
        width = min(max(64, w*scale), screen.width())
        height = min(max(64, h*scale), screen.height())
        if w*scale == width and h*scale == height:
            player_view.setFixedWidth(width)
            player_view.setFixedHeight(height)
            window.attach_player_view(window.pos())
            state['scale'] = scale

    return f


@scheme
def cycle_subtitles(player_view, vlc_main, state, show_action):
    def f():
        count = vlc_main.video_get_spu_count()
        if count <= 0:
            return

        # video_get_spu() work in a weird way,
        # so maintain the next spu manually.
        nxt = state['next_spu']
        ret = -1
        while ret != 0:
            ret = vlc_main.video_set_spu(nxt)
            if ret == 0:
                show_action('subtitles %d' % nxt)
            # How spu number is determined is not documented.
            # So just based on self experiments:
            # cycle: -1 <= spu <= get_spu_count()
            nxt = nxt + 1
            nxt = nxt if nxt <= count else -1
        state['next_spu'] = nxt

    return f


@scheme
def yank(clipbox, show_action):
    def f():
        s = clipbox.toPlainText()
        pyperclip.copy(s)
        show_action('yank')
    return f


@scheme
def yank_source(youtube, source, source_path, clip, show_action):
    def f():
        if youtube is None:
            clip(source_path)
        else:
            atag = '<a href="%s">%s</a>' % (source, youtube.title)
            clip(atag)
        show_action('yank-source')
    return f
