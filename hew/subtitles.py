from collections import OrderedDict
from pathlib import Path
import re

import click

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


@ scheme
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


@ scheme
def subtitles_map(main_vlc):
    return SubtitlesMap(main_vlc)


class SubtitlesMap:
    # -1 is a special value VLC uses to signify disabled.
    DISABLED = -1

    def __init__(self, main_vlc):
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
            code = vlc_name_to_code.get(name, '')
            d[spu] = (name, code)
        self.loaded_subtitles = d
        self.enabled = False

    def current(self):
        # Example data: (2, ('Korean', 'ko'))
        spu, info = self._first()
        return ((spu, info) if self.enabled else
                (self.DISABLED, info))  # Returns current selected subtitles info even though the subtitles are disabled

    def cycle(self):
        spu, _ = self._first()
        self.loaded_subtitles.move_to_end(spu)

    def _first(self):
        return next(iter(self.loaded_subtitles.items()))
