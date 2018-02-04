import sys

import click

import hew.action
import hew.core
import hew.qt5
import hew.vlc

from hew.util import Scheme


@click.command()
@click.option('--anki-media', envvar='ANKI_MEDIA')
@click.option('--convert-wav', is_flag=True)
@click.option('--srt', is_flag=True)
@click.option('--srt-path', type=click.Path(exists=True))
@click.option('--srt-padding', type=int, default=2000)
@click.argument('source-path', type=click.Path(exists=True))
def cli(anki_media,
        convert_wav,
        srt,
        srt_path,
        srt_padding,
        source_path):

    scheme = Scheme(hew.action.scheme,
                    hew.core.scheme,
                    hew.qt5.scheme,
                    hew.vlc.scheme)

    ctx = {
        'anki_media': anki_media,
        'convert_wav': convert_wav,
        'srt': srt,
        'srt_path': srt_path,
        'srt_padding': srt_padding,
        'source_path': source_path,
    }

    scheme.build(ctx)
    sys.exit(ctx['app'].exec_())


if __name__ == '__main__':
    cli()
