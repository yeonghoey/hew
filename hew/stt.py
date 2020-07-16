import wave

from google.cloud import speech_v1
from moviepy.editor import AudioFileClip

from hew.util import Scheme, tempfile_path

scheme = Scheme()


@scheme
def recognize_speech():
    def f(source_path, language_code='en-US'):
        wav_path = convert_to_wav(source_path)
        client = speech_v1.SpeechClient()
        config = {
            'language_code': language_code,
            'sample_rate_hertz': sample_rate_hertz(wav_path),
        }
        audio = {
            'content': content(wav_path),
        }
        response = client.recognize(config, audio)
        return compose_transcript(response)
    return f


def convert_to_wav(source_path):
    clip = AudioFileClip(source_path)
    wav_path = tempfile_path('.wav')
    # NOTE: -ac stands for 'audio channels'
    # Force mono since Google Cloud STT only accepts mono audio
    ffmpeg_params = ['-ac', '1']
    clip.write_audiofile(wav_path, ffmpeg_params=ffmpeg_params)
    return wav_path


def sample_rate_hertz(wav_path):
    with wave.open(wav_path, 'rb') as w:
        return w.getframerate()


def content(wav_path):
    with open(wav_path, 'rb') as f:
        return f.read()


def compose_transcript(response):
    def most_probable(result):
        # NOTE: According to `SpeechRecognitionResult` reference, the `alternatives`
        # will contain at least one recognition result, in the order of accuracy.
        # SEE: https://cloud.google.com/speech-to-text/docs/reference/rpc/google.cloud.speech.v1
        return result.alternatives[0].transcript

    return ' '.join(most_probable(result) for result in response.results)
