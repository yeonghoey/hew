import os
from urllib.parse import parse_qs, urlparse

import click
import moviepy.audio.fx.all as afx
from moviepy.editor import AudioFileClip, VideoFileClip
import pysrt
from pytube import YouTube

from hew.util import parse_timedelta, Scheme, tempfile_path, tempdir_path, downloads_path


scheme = Scheme()


@scheme
def youtube(yt, source):
    if yt:
        try:
            return YouTube(source)
        except Exception as e:
            raise RuntimeError('Failed to download YouTube Video')

    else:
        return None


@scheme
def source_path(youtube, yt_itag, source):
    if youtube is None:
        return source

    dir_ = downloads_path()
    stream = youtube.streams.get_by_itag(yt_itag)

    video_name = stream.default_filename
    video_path = os.path.join(dir_, video_name)

    click.secho("Download: '%s'" % (video_path), fg='yellow')
    stream.download(output_path=dir_)
    return video_path


@scheme
def main_path(source_path, download_yt_captions, convert_wav):
    if convert_wav:
        src = AudioFileClip(source_path)
        filename = os.path.basename(source_path)
        name, _ = os.path.splitext(filename)
        wav_path = os.path.join(tempdir_path(), name + '.wav')
        src.write_audiofile(wav_path)
        return wav_path
    else:
        return source_path


@scheme
def start_at_ms(start_at, yt, source):
    if start_at is None:
        start_at = '0'
        if yt:
            qs = urlparse(source).query
            q = parse_qs(qs)
            if 't' in q:
                # 'q' is a dict in form of '{key: list}'
                start_at = q['t'][0]

    if start_at != '0':
        click.secho('Start at: %s' % start_at, fg='yellow')
    return int(parse_timedelta(start_at) * 1000)


@scheme
def title(source_path):
    return os.path.basename(source_path)


@scheme
def video(main_path):
    _, ext = os.path.splitext(main_path)

    # FIXME: Hard coded to check whenter or not a file is video,
    # because I failed to figure out a proper way
    # to differenciate audio files from video files
    if ext in ('.m4a', '.mp3', '.wav'):
        return None
    else:
        # NOTE: This will be the default option
        # See https://github.com/Zulko/moviepy/issues/404#issuecomment-650461768
        return VideoFileClip(main_path, fps_source='fps')


@scheme
def audio(main_path):
    return AudioFileClip(main_path)


@scheme
def duration(audio):
    return int(audio.duration*1000)


@scheme
def clamp(duration):
    def f(ms):
        return min(max(ms, 0), duration)
    return f


@scheme
def state(video):
    return {
        'left': 0,
        'right': 0,
        'last_left': 0,
        'last_right': 0,
        'last_hewn_path': '',
        'last_hewn-side': 'left',
        'scale': 1.,
        'try_video': video is not None,  # Toggle with Tab
        'current_player': 'main',  # main or sub
        'current_target': 'anki',  # anki or downloads
        'before_jump': None,
    }
