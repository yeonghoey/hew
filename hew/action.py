import os
import shutil

import moviepy.audio.fx.all as afx
import pyperclip

from hew.util import (
    format_timedelta, format_timedelta_range, remove_tags, Scheme,
    tempfile_path, sha1of)


scheme = Scheme()


@scheme
def quit_(app, save_settings):
    def f():
        save_settings()
        app.exit()
    return f


@scheme
def toggle(main_vlc, sub_vlc, state, play, pause):
    def f():
        current_player = state['current_player']
        vlc_current = (main_vlc if current_player == 'main' else
                       sub_vlc)
        if vlc_current.is_playing():
            pause(vlc_current)
        else:
            play(vlc_current)
    return f


@scheme
def play(show_action):
    def f(vlc_player):
        vlc_player.play()
        show_action('play')

    return f


@scheme
def pause(show_action):
    def f(vlc_player):
        # NOTE: Use main_vlc.set_pause() instead of
        # main_vlc.pause(), which acts like toggle,
        # because it doesn't work consistently.
        vlc_player.set_pause(1)
        show_action('pause')
    return f


@scheme
def seek(main_vlc, clamp, show_action):
    def f(ms):
        t = main_vlc.get_time() + ms
        main_vlc.set_time(clamp(t))
        show_action('%+ds' % (ms/1000))
    return f


@scheme
def mark(main_vlc, state, show_action, update_mark):
    def f(side):
        assert side == 'left' or side == 'right'
        # NOTE: Ensure that newly marked hewn to be played at start(left).
        state['last_hewn_side'] = 'left'
        state[side] = main_vlc.get_time()
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
def hew(main_vlc,
        sub_vlc,
        anki,
        anki_media,
        video_no_sound,
        video_no_resize,
        main_view,
        video,
        audio,
        state,
        dump_media,
        play_hewn):

    dirname = anki_media if anki else '.'

    def f():
        left = state['left']
        right = state['right']
        if left >= right:
            return

        main_vlc.set_pause(1)
        if state['try_video'] and video is not None:
            hewn = subclip(video, left, right)
            temppath = tempfile_path('.mp4')
            ffmpeg_params = []
            if not video_no_resize:
                w, h = main_view.width(), main_view.height()
                # ffmpeg requires sizes to be even
                w, h = (w//2)*2, (h//2)*2
                ffmpeg_params.extend(['-vf', 'scale=%s:%s' % (w, h)])
            # Codecs chosen for HTML5
            hewn.write_videofile(temppath,
                                 codec='libx264',
                                 audio=not video_no_sound,
                                 audio_codec='aac',
                                 ffmpeg_params=ffmpeg_params)
            filename = sha1of(temppath) + '.mp4'
            filepath = os.path.join(dirname, filename)
            shutil.move(temppath, filepath)
            dump_media(filename)
        else:
            hewn = subclip(audio, left, right)
            temppath = tempfile_path('.mp3')
            hewn.write_audiofile(temppath)
            filename = sha1of(temppath) + '.mp3'
            filepath = os.path.join(dirname, filename)
            shutil.move(temppath, filepath)
            dump_media(filename)

        state['last_hewn_path'] = filepath
        state['last_left'] = left
        state['last_right'] = right
        play_hewn()

        # Seek to the right end
        main_vlc.set_time(right)

    return f


def subclip(clip, left, right):
    return (
        clip.subclip(left/1000., right/1000.)
            .fx(afx.audio_normalize)
    )


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
def play_hewn(main_vlc, sub_vlc, sub_view, state, set_current_player, show_action, right_duration):
    def f(side=None):
        path = state['last_hewn_path']
        side = state['last_hewn_side'] if side is None else side
        left = state['left']
        right = state['right']
        if not path:
            return

        set_current_player('sub')
        sub_vlc.set_mrl(path)
        sub_vlc.play()

        # NOTE: show sub_view only when it's available and
        # the hewn file is video. The best way to classify this would be to check
        # if there's video output on VLC. Found there's VLC API
        # 'vlc.libvlc_media_player_has_vout()' for checking that.
        # Unfortunately it doesn't work because "sub_vlc.set_mrl(path)" call is async call
        # and at this point the VLC player information is not updated.
        # Instead, as a workaround, checks whether the extension of the hewn file is mp4
        # because hewn files can only be either mp4 or mp3.
        if sub_view is not None:
            if path.endswith('.mp4'):
                sub_view.show()
                sub_view.raise_()
            else:
                sub_view.hide()

        duration = right - left
        if side == 'right' and duration != 0:
            # NOTE: For some reason, set_time() doesn't work properly,
            # while set_position() works as expected
            pos = max(0, duration - right_duration) / duration
            sub_vlc.set_position(pos)

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
def take_snapshot(state,
                  main_vlc,
                  main_view,
                  sub_vlc,
                  sub_view,
                  snapshot_dir,
                  clip_image,
                  show_action):

    def f():
        # NOTE: At least main_view should be valid
        if main_view is None:
            return

        # NOTE: sub_view may not be visible if the last hewn file was mp3.
        # take a snapshot of it when only it's visible.
        if (state['current_player'] == 'sub' and
                sub_view is not None and
                sub_view.isVisible()):
            vlc, view = sub_vlc, sub_view
        else:
            vlc, view = main_vlc, main_view

        path = tempfile_path('.png', snapshot_dir)
        w = view.width()
        h = view.height()
        vlc.video_take_snapshot(0, path, w, h)
        clip_image(path)
        show_action('take-snapshot')
    return f


@scheme
def reload_(main_vlc, main_path, show_action):
    def f():
        ms = main_vlc.get_time()
        main_vlc.set_mrl(main_path)
        main_vlc.play()
        main_vlc.set_time(ms)
        show_action('reload')
    return f


@scheme
def set_position(main_vlc):
    def f(ms):
        main_vlc.set_time(ms)
    return f


@scheme
def show_action(action_label):
    def f(s):
        action_label.setText(s)
    return f


@scheme
def set_current_player(state, current_player_label, main_vlc, main_view, sub_vlc, sub_view, slider):
    def f(s):
        assert s == 'main' or s == 'sub'
        if s == 'main':
            sub_vlc.stop()
            sub_view.hide()
            slider.setEnabled(True)
        if s == 'sub':
            main_vlc.set_pause(1)
            slider.setEnabled(False)

        state['current_player'] = s
        current_player_label.setText(s)

    return f


@scheme
def update_mark(mark_label):
    def f(l, r):
        s = format_timedelta_range(l, r)
        mark_label.setText(s)
    return f


@scheme
def resize(screen, window, main_view, sub_view, video, state):
    def f(x, absolute=False):
        if main_view is None:
            return
        if sub_view is None:
            return

        if absolute:
            scale = x
        else:
            scale = state['scale'] * x

        w, h = video.size
        width = min(max(64, w*scale), screen.width())
        height = min(max(64, h*scale), screen.height())
        if w*scale == width and h*scale == height:
            main_view.setFixedWidth(width)
            main_view.setFixedHeight(height)
            sub_view.setFixedWidth(width)
            sub_view.setFixedHeight(height)
            window.sync_view_positions(window.pos())
            state['scale'] = scale

    return f


@scheme
def cycle_subtitles(main_view, main_vlc, state, show_action):
    def f():
        count = main_vlc.video_get_spu_count()
        if count <= 0:
            return

        # video_get_spu() work in a weird way,
        # so maintain the next spu manually.
        nxt = state['next_spu']
        ret = -1
        while ret != 0:
            ret = main_vlc.video_set_spu(nxt)
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
