import os
import sys
import tempfile

import pyperclip
import pysrt
from moviepy.editor import AudioFileClip
import speech_recognition as sr

from hew.util import Scheme


scheme = Scheme()


@scheme
def audio(source_path):
    return AudioFileClip(source_path)


@scheme
def clamp(audio):
    def f(ms):
        return min(max(ms, 0), audio.duration*1000)
    return f


@scheme
def clip():
    def f(s):
        pyperclip.copy(s)
    return f


@scheme
def state():
    return {
        'left': 0,
        'right': 0,
        'last_left': 0,
        'last_right': 0,
        'last_hewed_path': '',
    }


@scheme
def subtitles(use_srt, srt_path, source_path):
    if srt_path is None:
        path = os.path.splitext(source_path)[0] + '.srt'
    if not use_srt:
        return None
    if not os.path.exists(path):
        sys.exit("'%s' does not exist" % path)
    return pysrt.open(path)


@scheme
def extract_subtitles(subtitles):
    def f(left, right, padding=1500):
        ss = subtitles.slice(starts_after=left-padding,
                             ends_before=right+padding)
        return ' '.join(s.text for s in ss)
    return f


@scheme
def recognize_hewed(state):
    def f(path):
        mp3 = AudioFileClip(path)
        _, wav_path = tempfile.mkstemp('.wav')
        mp3.write_audiofile(wav_path, verbose=False, progress_bar=False)

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            try:
                return r.recognize_google_cloud(audio)
            except (sr.RequestError, sr.UnknownValueError) as exc:
                return str(exc)
    return f
