from inspect import getargspec
import os
import re
import tempfile

import pytimeparse


class Scheme:
    def __init__(self, *schemes):
        self.targets = {}
        for scheme in schemes:
            for f in scheme.targets.values():
                self(f)

    def __call__(self, f):
        name = f.__name__

        if name in self.targets:
            raise RuntimeError("Name conflicts: '%s': (%r, %r)" %
                               (name, self.targets[name], f))
        self.targets[name] = f
        return f

    def build(self, ctx):
        next_ = dict(self.targets)
        while next_:
            targets, next_ = next_, {}
            for name, f in targets.items():
                ok = try_run(f, ctx)
                if not ok:
                    next_[name] = f
            if next_ == targets:
                raise RuntimeError("Cannot resolve dependencies: %r, %r" %
                                   (targets, ctx.keys()))


def try_run(f, ctx):
    argnames = getargspec(f)[0]
    try:
        kwargs = {k: ctx[k] for k in argnames}
        ctx[f.__name__] = f(**kwargs)
        return True
    # FIXME: If this KeyError is raised within the scheme function
    # This will cause an infinate loop.
    except KeyError:
        return False


def format_timedelta(ms1):
    s1, ms = divmod(ms1, 1000)
    m1, s = divmod(s1, 60)
    h, m = divmod(m1, 60)
    return '%d:%02d:%02d.%d' % (h, m, s, ms // 100)


def format_timedelta_range(left_ms, right_ms):
    ltd = format_timedelta(left_ms)
    rtd = format_timedelta(right_ms)
    return '%s ~ %s' % (ltd, rtd)


def parse_timedelta(s):
    return (try_seconds(s) or
            try_pytimeparse(s) or
            0)


def try_seconds(s):
    try:
        return float(s)
    except ValueError:
        return None


def try_pytimeparse(s):
    # pytimeparse.parse() returns None if it failed to parse.
    return pytimeparse.parse(s)


def remove_tags(s):
    # Just blindly remove all tags
    return re.sub(r'<[^>]*>', '', s)


def tempfile_path(ext, dir=None):
    fd, path = tempfile.mkstemp(ext, dir=dir)
    os.close(fd)
    return path


def tempdir_path():
    return tempfile.mkdtemp()
