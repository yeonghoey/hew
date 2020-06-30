import vlc

from hew.util import Scheme


scheme = Scheme()


@scheme
def vlc_instance(vlc_quiet):
    params = []
    if vlc_quiet:
        params.append('--quiet')
    return vlc.Instance(params)


@scheme
def vlc_main(vlc_instance,
             main_view,
             main_path,
             start_at_ms):
    p = vlc_instance.media_player_new(main_path)

    # NOTE: only support macOS currently
    if main_view is not None:
        nsview = int(main_view.winId())
        p.set_nsobject(nsview)
    p.play()
    p.set_time(start_at_ms)
    return p


@scheme
def vlc_sub(vlc_instance, sub_view):
    p = vlc_instance.media_player_new()
    if sub_view is not None:
        nsview = int(sub_view.winId())
        p.set_nsobject(nsview)
    return p
