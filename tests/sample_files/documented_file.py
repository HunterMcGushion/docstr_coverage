"""
This is a module docstring
"""


class FooBar:
    """
    This is a class-level docstring
    """

    def __init__(self):
        """
        This is a dunder method docstring
        """

    def function(self):
        """
        This is a regular method docstring
        """

    @property
    def prop(self):
        """
        This is a wrapped method docstring
        """

    @prop.setter
    def prop(self, value):
        """
        This is another wrapped method docstring
        """


def foo():
    """
    This is a function docstring
    """

    def _foo():
        """
        This is a nested function docstring
        """


def bar():
    """This is another function"""
