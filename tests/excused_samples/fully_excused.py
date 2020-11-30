""" Ignoring module docstrings is not yet supported. However, belows classes and functions docs are."""

import abc


# docstr_cov:excuse 'no one is reading this anyways'
class FooBar:

    # docstring_cov : excuse 'I'm super lazy'
    def __init__(self):
        pass

    @abc.abstractmethod
    #   docstring_cov:excuse '..., I really am...'
    def function(self):
        pass

    # docstring_coverage:excuse '...you can't imagine how much...'
    def prop(self):
        pass


# docstr_cov:excuse '... besides: who's checking anyways'
def bar():
    pass


# docstring_cov:excuse 'no one is reading this anyways'
class FooBarChild(FooBar):

    # docstr_cov:inherited
    def function(self):
        pass
