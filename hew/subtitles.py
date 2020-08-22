from collections import OrderedDict
from pathlib import Path
import re

import click
import pysrt

from hew.util import Scheme


scheme = Scheme()

# VLC register subtitles like "Track 1 - [English]"
# The name is determined by VLC on its own,
# so it's different from that of YouTube.
# The only way to handle it is to manually map these names.
LANGUAGES_INTERESTED_IN = [
    {'code': 'en', 'vlc_name': 'English'},
    {'code': 'en-GB', 'vlc_name': 'en-GB'},
    {'code': 'ko', 'vlc_name': 'Korean'},
]


@scheme
def download_yt_captions(youtube, source_path):
    if youtube is None:
        return

    captions_interested_in = (
        youtube.captions.get_by_language_code(l['code'])
        for l in LANGUAGES_INTERESTED_IN)

    existing_captions_interested_in = filter(
        lambda x: x is not None,
        captions_interested_in)

    video_path = Path(source_path)
    for caption in existing_captions_interested_in:
        name = video_path.stem
        caption_name = f'{name}.{caption.code}.srt'
        caption_path = video_path.parent / caption_name
        click.secho("Download: '%s'" % caption_path, fg='yellow')
        with open(caption_path, 'w') as f:
            try:
                f.write(caption.generate_srt_captions())
            except Exception as exc:
                click.secho("Failed to download srt: '%s'" %
                            str(exc), fg='red')


@scheme
def subtitles_map(source_path, main_vlc):
    return SubtitlesMap(source_path, main_vlc)


class SubtitlesMap:
    # -1 is a special value VLC uses to signify disabled.
    DISABLED = -1

    def __init__(self, source_path, main_vlc):
        self.enabled = False

        video_path = Path(source_path)
        self._dir = video_path.parent
        self._stem = video_path.stem

        vlc_name_to_code = {l['vlc_name']: l['code']
                            for l in LANGUAGES_INTERESTED_IN}
        d = OrderedDict()
        for spu, bdesc in main_vlc.video_get_spu_description():
            if spu == self.DISABLED:
                continue
            desc = bdesc.decode('utf-8')
            # VLC register subtitles like "Track 1 - [English]"
            m = re.match(r'^Track \d+ - \[(?P<name>[^\]]+)\]', desc)
            name = m.group('name') if m else 'default'
            code = vlc_name_to_code.get(name, None)
            srt_path = (self._dir / f'{self._stem}.srt' if code is None else
                        self._dir / f'{self._stem}.{code}.srt')
            srt = pysrt.open(str(srt_path)) if srt_path.exists() else None
            click.secho("SRT: '%s'" % srt_path, fg='yellow')
            d[spu] = (name, srt)
        self._loaded_subtitles = d

    def current(self):
        # Example data: (2, ('Korean', 'ko'))
        spu, spec = self._first()
        return ((spu, spec) if self.enabled else
                (self.DISABLED, spec))  # Returns current selected subtitles spec even though the subtitles are disabled

    def is_loaded(self):
        return bool(self._loaded_subtitles)

    def cycle(self):
        spu, _ = self._first()
        if self._loaded_subtitles:
            self._loaded_subtitles.move_to_end(spu)

    def _first(self):
        if self._loaded_subtitles:
            return next(iter(self._loaded_subtitles.items()))
        else:
            return (-1, ('default', None))
