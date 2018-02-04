import vlc

from hew.util import Scheme


scheme = Scheme()


@scheme
def vlc_instance(video_sub):
    params = []
    if not video_sub:
        params.append('--no-sub-autodetect-file')
    return vlc.Instance(params)


@scheme
def vlc_main(vlc_instance, player_view, main_path):
    p = vlc_instance.media_player_new(main_path)

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
