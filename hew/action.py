from collections import OrderedDict
import os
from pathlib import Path
import shutil

import moviepy.audio.fx.all as afx
import pyperclip
import pysrt

from hew.util import (
    format_timedelta, format_timedelta_range, remove_tags, Scheme,
    tempfile_path, downloads_path, sha1of)


scheme = Scheme()


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
        get_current_target_path,
        video_no_sound,
        video_no_resize,
        main_view,
        video,
        audio,
        state,
        compose_subtitles_baked_clip,
        srt_padding,
        clip_anki,
        clip_downloads,
        play_hewn):

    def f():
        dirname = get_current_target_path()
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

            composed = compose_subtitles_baked_clip(
                hewn, left, right, srt_padding, state['bg_under_subtitles'])

            # Codecs chosen for HTML5
            composed.write_videofile(temppath,
                                     codec='libx264',
                                     audio=not video_no_sound,
                                     audio_codec='aac',
                                     ffmpeg_params=ffmpeg_params)
            filename = sha1of(temppath) + '.mp4'
            filepath = os.path.join(dirname, filename)
            shutil.move(temppath, filepath)
            if state['current_target'] == 'anki':
                clip_anki(filename)
            else:
                clip_downloads(filepath)
        else:
            hewn = subclip(audio, left, right)
            temppath = tempfile_path('.mp3')
            hewn.write_audiofile(temppath)
            filename = sha1of(temppath) + '.mp3'
            filepath = os.path.join(dirname, filename)
            shutil.move(temppath, filepath)
            if state['current_target'] == 'anki':
                clip_anki(filename)
            else:
                clip_downloads(filepath)

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
def clip_anki(clip, show_action):
    def f(filename):
        sound_str = '[sound:%s]' % filename
        clip(sound_str)
        show_action('clip-anki')

    return f


@scheme
def clip_downloads(clip, show_action):
    def f(filepath):
        clip(filepath)
        show_action('clip-downloads')

    return f


@scheme
def dump_srt(state,
             subtitles_pri_map,
             srt_padding,
             clip,
             show_action):

    def f():
        path = state['last_hewn_path']
        if not path:
            return

        spu, spec = subtitles_pri_map.current()
        _, srt = spec
        if srt is None:
            return

        left = state['left']
        right = state['right']
        ss = srt.slice(starts_after=left - srt_padding,
                       ends_before=right + srt_padding)
        transcript = ' '.join(remove_tags(s.text) for s in ss)
        clip(transcript.strip())
        show_action('dump-srt')

    return f


@scheme
def dump_recognized(state,
                    recognize_speech,
                    clip,
                    show_action):

    def f():
        path = state['last_hewn_path']
        if not path:
            return

        transcript = recognize_speech(path)
        clip(transcript.strip())
        show_action('dump-recognized')
    return f


@scheme
def dump_primary(subtitles_pri_map, dump_srt, dump_recognized):
    # NOTE: if subtitles exist, dump_srt should be primary
    return (dump_srt if subtitles_pri_map.is_loaded() else
            dump_recognized)


@scheme
def dump_secondary(subtitles_pri_map, dump_primary, dump_srt, dump_recognized):
    assert dump_primary in (dump_srt, dump_recognized)
    return (dump_recognized if dump_primary == dump_srt else dump_srt)


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
        show_action('%s' % filename)
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
def reload_(main_vlc, main_path, set_current_player, subtitles_pri_map, show_action):
    def f():
        ms = main_vlc.get_time()
        main_vlc.set_mrl(main_path)
        main_vlc.play()
        main_vlc.set_time(ms)

        spu, _ = subtitles_pri_map.current()
        main_vlc.video_set_spu(spu)

        set_current_player('main')
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
def set_current_player(state, current_player_label, main_vlc, main_view, sub_vlc, sub_view, slider,
                       label_style_normal, label_style_notice):
    def f(s):
        assert s == 'main' or s == 'sub'

        if s == 'main':
            sub_vlc.stop()
            sub_view.hide()
            slider.setEnabled(True)
            label_style_normal(current_player_label)

        if s == 'sub':
            main_vlc.set_pause(1)
            slider.setEnabled(False)
            label_style_notice(current_player_label)

        state['current_player'] = s
        current_player_label.setText(s)

    return f


@scheme
def target_paths(anki_media):
    return {
        'anki': anki_media,
        'downloads': downloads_path(),
    }


@scheme
def set_current_target(state, current_target_label, label_style_color):
    def f(target):
        if target == 'anki':
            label_style_color(current_target_label, 'red')
        if target == 'downloads':
            label_style_color(current_target_label, 'blue')

        current_target_label.setText(target)
        state['current_target'] = target
    return f


@scheme
def toggle_current_target(state, set_current_target):
    def f():
        t = state['current_target']
        set_current_target('downloads' if t == 'anki' else 'anki')
    return f


@scheme
def get_current_target_path(state, target_paths):
    def f():
        return target_paths[state['current_target']]
    return f


@scheme
def update_mark(mark_label):
    def f(l, r):
        td_range = format_timedelta_range(l, r)
        td_duration = (format_timedelta(r-l) if r-l > 0 else
                       '-')
        text = '%s (%s)' % (td_range, td_duration)
        mark_label.setText(text)
    return f


@scheme
def init_mark_label(update_mark):
    update_mark(0, 0)
    return None


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


BOOKMARK_EPSILON = 2.0


@scheme
def prev_bookmark(main_vlc, bookmarks, state, clamp, show_action):
    def f():
        if bookmarks is None:
            return
        current = main_vlc.get_time() / 1000
        prev_s = current
        for s in bookmarks:
            if s + BOOKMARK_EPSILON > current:
                break
            prev_s = s
        # Only keep before_jump when current not in bookmarks
        if all(map(lambda s: abs(current - s) > BOOKMARK_EPSILON, bookmarks)):
            state['before_jump'] = current
        main_vlc.set_time(clamp(int(prev_s * 1000)))
        show_action('prev_bookmark')
    return f


@scheme
def next_bookmark(main_vlc, bookmarks, state, clamp, show_action):
    def f():
        if bookmarks is None:
            return
        current = main_vlc.get_time() / 1000
        next_s = current
        for s in reversed(bookmarks):
            if s - BOOKMARK_EPSILON < current:
                break
            next_s = s
        # Only keep before_jump when current not in bookmarks
        if all(map(lambda s: abs(current - s) > BOOKMARK_EPSILON, bookmarks)):
            state['before_jump'] = current
        main_vlc.set_time(clamp(int(next_s * 1000)))
        show_action('next_bookmark')
    return f


@scheme
def return_before_jump(main_vlc, state, clamp, show_action):
    def f():
        before_jump = state['before_jump']
        if before_jump is None:
            return
        main_vlc.set_time(clamp(int(before_jump * 1000)))
        show_action('return_before_jump')
    return f


@scheme
def move_to_start(main_vlc, state, show_action):
    def f():
        current = main_vlc.get_time() / 1000
        if current < BOOKMARK_EPSILON:
            return
        state['before_jump'] = current
        main_vlc.set_time(0)
        show_action('move_to_start')
    return f


@scheme
def toggle_subtitles(main_view, main_vlc, subtitles_pri_map, show_action, update_subtitles_pri_label):
    # Disable by default
    subtitles_pri_map.enabled = False
    main_vlc.video_set_spu(-1)
    update_subtitles_pri_label()

    def f():
        subtitles_pri_map.enabled = not subtitles_pri_map.enabled
        spu, spec = subtitles_pri_map.current()
        main_vlc.video_set_spu(spu)
        status = 'enabled' if subtitles_pri_map.enabled else 'disabled'
        show_action(f'subtitles_pri: {status}')
        update_subtitles_pri_label()
    return f


@scheme
def cycle_subtitles(main_view, main_vlc, subtitles_pri_map, show_action, toggle_subtitles, update_subtitles_pri_label):
    def f():
        subtitles_pri_map.cycle()
        spu, spec = subtitles_pri_map.current()
        name, _ = spec
        main_vlc.video_set_spu(spu)
        show_action(f'subtitles_pri: {name}')
        update_subtitles_pri_label()
    return f


@scheme
def toggle_subtitles_aux(main_view, subtitles_aux_map, show_action, update_subtitles_aux_label):
    # Disable by default
    subtitles_aux_map.enabled = False
    update_subtitles_aux_label()

    def f():
        subtitles_aux_map.enabled = not subtitles_aux_map.enabled
        status = 'enabled' if subtitles_aux_map.enabled else 'disabled'
        show_action(f'subtitles_aux: {status}')
        update_subtitles_aux_label()
    return f


@scheme
def cycle_subtitles_aux(main_view, subtitles_aux_map, show_action, toggle_subtitles_aux, update_subtitles_aux_label):
    def f():
        subtitles_aux_map.cycle()
        _, spec = subtitles_aux_map.current()
        name, _ = spec
        show_action(f'subtitles_aux: {name}')
        update_subtitles_aux_label()

    return f


@scheme
def toggle_bg_under_subtitles(state, update_subtitles_pri_label, update_subtitles_aux_label, show_action):
    def f():
        state['bg_under_subtitles'] = not state['bg_under_subtitles']
        update_subtitles_pri_label()
        update_subtitles_aux_label()
        show_action(f'bg_under_subtitles: {state["bg_under_subtitles"]}')
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
