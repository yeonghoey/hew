import vlc

from hew.util import Scheme


scheme = Scheme()


@scheme
def vlc_instance():
    params = []
    return vlc.Instance(params)


@scheme
def vlc_main(vlc_instance,
             player_view,
             main_path,
             start_at_ms):
    p = vlc_instance.media_player_new(main_path)

    # NOTE: only support macOS currently
    if player_view is not None:
        nsview = int(player_view.winId())
        p.set_nsobject(nsview)
    p.play()
    p.set_time(start_at_ms)
    return p


@scheme
def vlc_sub(vlc_instance):
    p = vlc_instance.media_player_new()
    return p
