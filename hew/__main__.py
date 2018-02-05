import sys

import click

import hew.action
import hew.core
import hew.qt5
import hew.vlc

from hew.util import Scheme


@click.command()
@click.option('--anki-media', envvar='ANKI_MEDIA')
@click.option('--yt', is_flag=True)
@click.option('--yt-itag', default=18, type=int, help='18: 360p, 22: 720p,...')
@click.option('--yt-lang', default='en', help='for caption, such as "en"')
@click.option('--convert-wav', is_flag=True)
@click.option('--srt', is_flag=True)
@click.option('--srt-path', type=click.Path(exists=True))
@click.option('--srt-padding', type=int, default=2000)
@click.argument('source')
@click.argument('start-at', default=None, required=False)
def cli(anki_media,
        yt,
        yt_itag,
        yt_lang,
        convert_wav,
        srt,
        srt_path,
        srt_padding,
        source,
        start_at):

    scheme = Scheme(hew.action.scheme,
                    hew.core.scheme,
                    hew.qt5.scheme,
                    hew.vlc.scheme)

    ctx = {
        'anki_media': anki_media,
        'yt': yt,
        'yt_itag': yt_itag,
        'yt_lang': yt_lang,
        'convert_wav': convert_wav,
        'srt': srt,
        'srt_path': srt_path,
        'srt_padding': srt_padding,
        'source': source,
        'start_at': start_at,
    }

    scheme.build(ctx)
    sys.exit(ctx['app'].exec_())


if __name__ == '__main__':
    cli()
