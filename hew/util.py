from inspect import getargspec


class Scheme:
    def __init__(self, *schemes):
        self.targets = {}
        for scheme in schemes:
            for f in scheme.targets.values():
                self(f)

    def __call__(self, f):
        name = f.__name__

        if name in self.targets:
            raise RuntimeError('Name conflicts: "%s": (%r, %r)' %
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
                raise RuntimeError('Cannot resolve dependencies: %r, %r' %
                                   (targets, ctx.keys()))


def try_run(f, ctx):
    argnames = getargspec(f)[0]
    try:
        kwargs = {k: ctx[k] for k in argnames}
        ctx[f.__name__] = f(**kwargs)
        return True
    except KeyError:
        return False
