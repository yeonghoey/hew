from functools import wraps
from inspect import getargspec


class Context:
    def __init__(self):
        self.targets = {}

    def __call__(self, f):
        self.targets[f.__name__] = f
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
                raise ValueError('Cannot resolve dependencies: %r', targets)


def try_run(f, ctx):
    argnames = getargspec(f)[0]
    try:
        kwargs = {k: ctx[k] for k in argnames}
        ctx[f.__name__] = f(**kwargs)
        return True
    except KeyError:
        return False
