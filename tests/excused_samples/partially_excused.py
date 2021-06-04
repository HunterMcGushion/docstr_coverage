"""This is a module docstring"""

import abc


# docstr-coverage:excuse `no one is reading this anyways`
class FooBar:
    def __init__(self):
        pass

    # docstr-coverage:excuse `..., I really am...`
    @abc.abstractmethod
    def function(self):
        pass

    # docstr-coverage:excuse `...you can't imagine how much...`
    def prop(self):
        pass


def bar():
    pass


class FooBarChild(FooBar):
    """Wow! A docstring. Crazy"""

    # docstr-coverage:inherited
    def function(self):
        pass
