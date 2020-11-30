""" Ignoring module docstrings is not yet supported. However, belows classes and functions docs are."""

import abc


# docstring_cov:excuse 'no one is reading this anyways'
class FooBar:
    def __init__(self):
        pass

    @abc.abstractmethod
    #   docstring_cov:excuse '..., I really am...'
    def function(self):
        pass

    # docstring_coverage:excuse '...you can't imagine how much...'
    def prop(self):
        pass


def bar():
    pass


class FooBarChild(FooBar):
    """ Wow! A docstring. Crazy """

    # docstr_cov:inherited
    def function(self):
        pass
