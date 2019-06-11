import os
from urllib.parse import parse_qs, urlparse

import click
from moviepy.editor import AudioFileClip, VideoFileClip
import pysrt
from pytube import YouTube
import speech_recognition as sr

from hew.util import parse_timedelta, Scheme, tempfile_path, tempdir_path


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
def source_path(youtube, yt_itag, yt_lang, source):
    if youtube is None:
        return source

    dir_ = tempdir_path()
    stream = youtube.streams.get_by_itag(yt_itag)

    video_name = stream.default_filename
    video_path = os.path.join(dir_, video_name)

    click.secho("Download: '%s'" % (video_path), fg='yellow')
    stream.download(output_path=dir_)

    caption = youtube.captions.get_by_language_code(yt_lang)
    if caption is not None:
        name, _ = os.path.splitext(video_name)
        caption_name = '%s.srt' % name
        caption_path = os.path.join(dir_, caption_name)
        click.secho("Download: '%s'" % caption_path, fg='yellow')
        with open(caption_path, 'w') as f:
            try:
                f.write(caption.generate_srt_captions())
            except Exception as exc:
                click.secho("Failed to download srt: '%s'" % str(exc),
                            fg='red')

    return video_path


@scheme
def main_path(source_path, convert_wav):
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
        return VideoFileClip(main_path)


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
def state():
    return {
        'left': 0,
        'right': 0,
        'last_left': 0,
        'last_right': 0,
        'last_hewn_path': '',
        'last_hewn-side': 'left',
        'scale': 1.,
        'next_spu': -1,  # Disabled
    }


@scheme
def subtitles(source_path):
    path = os.path.splitext(source_path)[0] + '.srt'
    if os.path.exists(path):
        click.secho("SRT: '%s'" % path, fg='yellow')
        return pysrt.open(path)
    else:
        return None


@scheme
def recognize_hewn(state):
    def f(path):
        mp3 = AudioFileClip(path)
        wav_path = tempfile_path('.wav')
        mp3.write_audiofile(wav_path, verbose=False, progress_bar=False)

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            try:
                return r.recognize_google_cloud(audio)
            except Exception as exc:
                click.secho(str(exc), fg='red')
                return ''
    return f
