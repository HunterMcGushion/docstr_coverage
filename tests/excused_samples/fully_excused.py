""" Ignoring module docstrings is not yet supported.
However, belows classes and functions docs are."""

import abc


# docstr-coverage:excuse `no one is reading this anyways`
class FooBar:

    # docstr-coverage : excuse `I'm super lazy`
    def __init__(self):
        pass

    #   docstr-coverage:excuse `..., I really am...`
    @abc.abstractmethod
    def function(self):
        pass

    # docstr-coverage:excuse `...you can't imagine how much...`
    def prop(self):
        pass


# docstr-coverage:excuse `... besides: who's checking anyways`
def bar():
    pass


# docstr-coverage:excuse `no one is reading this anyways`
class FooBarChild(FooBar):

    # docstr-coverage:inherited
    def function(self):
        pass
