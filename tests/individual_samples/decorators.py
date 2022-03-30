"""Test file for ignored getters and setters"""


class C:
    """Example class taken from https://docs.python.org/3/library/functions.html#property."""

    def __init__(self):
        """The __init__ is documented."""
        self._x = None

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @x.deleter
    def x(self):
        del self._x
