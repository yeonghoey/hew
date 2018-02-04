import os
import sys

import pysrt
from moviepy.editor import AudioFileClip, VideoFileClip
import speech_recognition as sr

from hew.util import Scheme, temppath, tempdir


scheme = Scheme()


@scheme
def main_path(source_path, convert_wav):
    if convert_wav:
        src = AudioFileClip(source_path)
        filename = os.path.basename(source_path)
        name, _ = os.path.splitext(filename)
        wav_path = os.path.join(tempdir(), name + '.wav')
        src.write_audiofile(wav_path)
        return wav_path
    else:
        return source_path


@scheme
def title(source_path):
    return os.path.basename(source_path)


@scheme
def video(main_path):
    _, ext = os.path.splitext(main_path)

    # FIXME: Hard coded to check whenter or not a file is video,
    # because I failed to figure out a proper way
    # to differenciate audio files from video files
    if ext in ('.mp3', '.wav'):
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
        'scale': 1.,
        'next_spu': -1,  # Disabled
    }


@scheme
def subtitles(srt, srt_path, source_path):
    if srt_path is None:
        path = os.path.splitext(source_path)[0] + '.srt'
    if not srt:
        return None
    if not os.path.exists(path):
        sys.exit("'%s' does not exist" % path)
    return pysrt.open(path)


@scheme
def extract_subtitles(subtitles, srt_padding):
    def f(left, right):
        ss = subtitles.slice(starts_after=left - srt_padding,
                             ends_before=right + srt_padding)
        return ' '.join(s.text for s in ss)
    return f


@scheme
def recognize_hewn(state):
    def f(path):
        mp3 = AudioFileClip(path)
        wav_path = temppath('.wav')
        mp3.write_audiofile(wav_path, verbose=False, progress_bar=False)

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            try:
                return r.recognize_google_cloud(audio)
            except (sr.RequestError, sr.UnknownValueError) as exc:
                return str(exc)
    return f
