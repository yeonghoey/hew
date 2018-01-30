import vlc

from hew.util import Scheme


scheme = Scheme()


@scheme
def vlc_instance():
    # Disable subtitles because they slow down the player for unknown reason
    return vlc.Instance('--no-sub-autodetect-file')


@scheme
def vlc_main(vlc_instance, player_view, source_path):
    p = vlc_instance.media_player_new(source_path)

    # NOTE: only support macOS currently
    if player_view is not None:
        nsview = int(player_view.winId())
        p.set_nsobject(nsview)
    p.play()
    return p


@scheme
def vlc_sub(vlc_instance):
    p = vlc_instance.media_player_new()
    return p
