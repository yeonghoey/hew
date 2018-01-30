import os
import sys
import tempfile

import pysrt
from moviepy.editor import AudioFileClip, VideoFileClip
import speech_recognition as sr

from hew.util import Scheme


scheme = Scheme()


@scheme
def title(source_path):
    return os.path.basename(source_path)


@scheme
def video(source_path):
    _, ext = os.path.splitext(source_path)

    # FIXME: Hard coded to check whenter or not a file is video,
    # because I failed to figure out a proper way
    # to differenciate audio files from video files
    if ext in ('.mp3', '.wav'):
        return None
    else:
        return VideoFileClip(source_path)


@scheme
def audio(source_path):
    return AudioFileClip(source_path)


@scheme
def player_default_size(video, screen):
    # Determine the base size based on the media
    # When it's audio, just set zero
    if video is None:
        return None

    w, h = video.size
    # For convenience, do not let the deault size
    # be larger than half the screen size
    sw, sh = screen.width(), screen.height()
    while w > sw*.5 or h > sh*.5:
        w, h = w*.5, h*.5

    return (w, h)


@scheme
def duration(audio):
    return audio.duration*1000


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
