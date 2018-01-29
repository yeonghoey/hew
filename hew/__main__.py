import sys

import click

import hew.action
import hew.core
import hew.qt5
import hew.vlc

from hew.util import Scheme


@click.command()
@click.option('--anki-media', envvar='ANKI_MEDIA')
@click.option('--use-srt', is_flag=True)
@click.option('--srt-path', type=click.Path(exists=True))
@click.argument('source-path', type=click.Path(exists=True))
def cli(anki_media, use_srt, srt_path, source_path):

    scheme = Scheme(hew.action.scheme,
                    hew.core.scheme,
                    hew.qt5.scheme,
                    hew.vlc.scheme)

    ctx = {
        'anki_media': anki_media,
        'use_srt': use_srt,
        'srt_path': srt_path,
        'source_path': source_path,
    }

    scheme.build(ctx)

    sys.exit(ctx['app'].exec_())


if __name__ == '__main__':
    cli()
