from collections import OrderedDict
from io import StringIO
from pathlib import Path
import re

import click
from moviepy.editor import CompositeVideoClip, TextClip
from moviepy.video.tools.subtitles import SubtitlesClip
import pysrt

from hew.util import Scheme, tempfile_path


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
def subtitles_pri_map(source_path, main_vlc):
    return SubtitlesMap(source_path, main_vlc)


@scheme
def subtitles_aux_map(source_path, main_vlc):
    x = SubtitlesMap(source_path, main_vlc)
    x.cycle()
    return x


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


@scheme
def compose_subtitles_baked_clip(subtitles_pri_map, subtitles_aux_map):
    def f(hewn, left, right, srt_padding):
        clips = [hewn]
        main_sub = make_subtitlesclip(
            subtitles_pri_map, hewn.size, left, right, srt_padding, vpos='bottom')
        if main_sub is not None:
            clips.append(main_sub)
        aux_sub = make_subtitlesclip(
            subtitles_aux_map, hewn.size, left, right, srt_padding, vpos='top')
        if aux_sub is not None:
            clips.append(aux_sub)
        return CompositeVideoClip(clips)

    return f


def make_subtitlesclip(subtitles_map, hewn_size, left, right, srt_padding, vpos):
    spu, spec = subtitles_map.current()
    if spu == -1:
        return None

    _, srt = spec
    subsrt_path = subsrt(srt, left, right, srt_padding)
    if subsrt_path is None:
        return None

    w, h = hewn_size
    # NOTE: Stick to the screen edge when using bg,
    # put some margins otherwise.
    size = (int(w*0.8), None)
    margin_h = int(h * 0.05)

    def make_textclip(txt):
        # NOTE: imagemagick may fail to retrieve the font, 'ArialUnicode', configured here.
        # To make sure 'ArialUnicode' exists,
        # check '/usr/local/Cellar/imagemagick/7.0.10-28/etc/ImageMagick-7/type.xml'
        # and add a font declaration like:
        # <type
        #   format="ttf"
        #   name="ArialUnicode"
        #   fullname="Arial Unicode MS"
        #   family="Arial Unicode"
        #   glyphs="/System/Library/Fonts/Supplemental/Arial Unicode.ttf" />
        # To check if it's correctly configuared:
        # python -c 'from moviepy.editor import TextClip; print(TextClip.list("font"))'
        return TextClip(txt, size=size,
                        method='caption', align='center',
                        font='ArialUnicode', fontsize=36, color='white',
                        bg_color='rgba(0,0,0,0.6)')

    subtitlesclip = SubtitlesClip(subsrt_path, make_textclip)

    def blit_on(self, picture, t):
        # Monkey patch 'blit_on' to place subtitle relative to its dynamic size
        # The block below copied from moviepy.
        #################################################################################################
        hf, wf = framesize = picture.shape[:2]

        if self.ismask and picture.max():
            return np.minimum(1, picture + self.blit_on(np.zeros(framesize), t))

        ct = t - self.start  # clip time

        # GET IMAGE AND MASK IF ANY

        img = self.get_frame(ct)
        mask = self.mask.get_frame(ct) if self.mask else None

        if mask is not None and ((img.shape[0] != mask.shape[0]) or (img.shape[1] != mask.shape[1])):
            img = self.fill_array(img, mask.shape)

        hi, wi = img.shape[:2]
        #################################################################################################
        pos_x = (wf - wi) / 2  # center
        pos_y = margin_h if vpos == 'top' else (hf - hi - margin_h)
        pos = map(int, (pos_x, pos_y))
        from moviepy.video.tools.drawing import blit
        return blit(img, picture, pos, mask=mask, ismask=self.ismask)

    subtitlesclip.blit_on = blit_on.__get__(subtitlesclip)
    return subtitlesclip


def subsrt(srt, left, right, srt_padding):
    sliced = srt.slice(starts_after=left - srt_padding,
                       ends_before=right + srt_padding)
    if not sliced:
        return None

    # NOTE: The result of slice still references srt items in
    # the original srt. There seems no way a way to deep copy,
    # So export as a text and recreate from it.
    buf = StringIO()
    sliced.write_into(buf)
    ss = pysrt.from_string(buf.getvalue())

    # Do some modifications on it.
    ss.clean_indexes()
    ss.shift(milliseconds=-left)
    path = tempfile_path('.srt')
    ss.save(path, encoding='utf-8')
    return path
