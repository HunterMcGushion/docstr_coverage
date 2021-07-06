"""Module containing a single utility data class: IgnoreConfig"""
from typing import List, Tuple


class IgnoreConfig:
    """Data class storing information about docstring types to ignore when aggregating coverage"""

    def __init__(
        self,
        ignore_names: Tuple[List[str], ...] = (),
        skip_magic: bool = False,
        skip_file_docstring: bool = False,
        skip_init: bool = False,
        skip_class_def: bool = False,
        skip_private: bool = False,
        skip_property: bool = False,
        skip_setter: bool = True,
        skip_deleter: bool = True,
    ):
        self._ignore_names = ignore_names
        self._skip_magic = skip_magic
        self._skip_file_docstring = skip_file_docstring
        self._skip_init = skip_init
        self._skip_class_def = skip_class_def
        self._skip_private = skip_private
        self._skip_property = skip_property
        self._skip_setter = skip_setter
        self._skip_deleter = skip_deleter

    @property
    def ignore_names(self):
        """Patterns to ignore when checking documentation. Each list in `ignore_names` defines a
        different pattern to be ignored. The first element in each list is the regular expression
        for matching filenames. All remaining arguments in each list are regexes for matching names
        of functions/classes. A node is ignored if it matches the filename regex and at least one
        of the remaining regexes"""
        return self._ignore_names

    @property
    def skip_magic(self):
        """If True, skip all magic methods (methods with both leading and trailing double
        underscores), except `__init__` and exclude them from the report"""
        return self._skip_magic

    @property
    def skip_file_docstring(self):
        """If True, skip check for a module-level docstring"""
        return self._skip_file_docstring

    @property
    def skip_init(self):
        """If True, skip methods named `__init__` and exclude them from the report"""
        return self._skip_init

    @property
    def skip_class_def(self):
        """If True, skip class definition docstrings and exclude them from the report. If this is
        True, the class's methods will still be checked"""
        return self._skip_class_def

    @property
    def skip_private(self):
        """If True, skip function definitions beginning with a single underscore."""
        return self._skip_private

    @property
    def skip_property(self):
        """If True, skip nodes with `@property` decorator."""
        return self._skip_property

    @property
    def skip_setter(self):
        """If True, skip nodes with `@setter` decorator."""
        return self._skip_setter

    @property
    def skip_deleter(self):
        """If True, skip nodes with `@deleter` decorator."""
        return self._skip_deleter
