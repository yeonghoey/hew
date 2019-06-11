import sys

import click

import hew.action
import hew.core
import hew.qt5
import hew.vlc

from hew.util import Scheme


DIR = click.Path(exists=True, file_okay=False, dir_okay=True)


@click.command()
@click.option('--anki', is_flag=True)
@click.option('--anki-media', type=DIR, envvar='ANKI_MEDIA')
@click.option('--video-on-rmark', is_flag=True)
@click.option('--video-no-sound', is_flag=True)
@click.option('--video-as-playersize', is_flag=True)
@click.option('--yt', is_flag=True)
@click.option('--yt-quality', default='720p', help='one of 360p, 720p, 1080p')
@click.option('--yt-itag', default=None, type=int, help='overrides yt-quality')
@click.option('--yt-lang', default='en', help='for caption, such as "en"')
@click.option('--right-duration', type=int, default=1000)
@click.option('--convert-wav', is_flag=True)
@click.option('--snapshot-dir', type=DIR)
@click.option('--srt-padding', type=int, default=2000)
@click.option('--vlc-quiet/--vlc-no-quiet', default=True)
@click.argument('source')
@click.argument('start-at', default=None, required=False)
def cli(anki,
        anki_media,
        video_on_rmark,
        video_no_sound,
        video_as_playersize,
        yt,
        yt_quality,
        yt_itag,
        yt_lang,
        right_duration,
        convert_wav,
        snapshot_dir,
        srt_padding,
        vlc_quiet,
        source,
        start_at):

    scheme = Scheme(hew.action.scheme,
                    hew.core.scheme,
                    hew.qt5.scheme,
                    hew.vlc.scheme)

    if yt_itag is None:
        # https://gist.github.com/sidneys/7095afe4da4ae58694d128b1034e01e2
        mapping = {'360p': 18, '720p': 22, '1080p': 37}
        yt_itag = mapping[yt_quality]
    ctx = {
        'anki': anki,
        'anki_media': anki_media,
        'video_on_rmark': video_on_rmark,
        'video_no_sound': video_no_sound,
        'video_as_playersize': video_as_playersize,
        'yt': yt,
        'yt_itag': yt_itag,
        'yt_lang': yt_lang,
        'right_duration': right_duration,
        'convert_wav': convert_wav,
        'snapshot_dir': snapshot_dir,
        'srt_padding': srt_padding,
        'vlc_quiet': vlc_quiet,
        'source': source,
        'start_at': start_at,
    }

    scheme.build(ctx)
    sys.exit(ctx['app'].exec_())


if __name__ == '__main__':
    cli()
