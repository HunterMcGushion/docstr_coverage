"""Module containing a single utility data class: IgnoreConfig"""
from typing import List, Tuple


class IgnoreConfig:
    """An immutable data class, storing information about which types of
    docstrings should be ignored when aggregating coverage."""

    def __init__(
        self,
        skip_magic: bool = False,
        skip_file_docstring: bool = False,
        skip_init: bool = False,
        skip_class_def: bool = False,
        skip_private: bool = False,
        ignore_names: Tuple[List[str], ...] = (),
    ):
        self._skip_magic = skip_magic
        self._skip_file_docstring = skip_file_docstring
        self._skip_init = skip_init
        self._skip_class_def = skip_class_def
        self._skip_private = skip_private
        self._ignore_names = ignore_names

    @property
    def skip_magic(self):
        """If True, skip all magic methods (double-underscore-prefixed),
            except '__init__' and does not include them in the report."""
        return self._skip_magic

    @property
    def skip_file_docstring(self):
        """If True, skip check for a module-level docstring."""
        return self._skip_file_docstring

    @property
    def skip_init(self):
        """If True, skip methods named '__init__' and does not include
            them in the report."""
        return self._skip_init

    @property
    def skip_class_def(self):
        """If True, skip class definitions and does not include them in the report.
            If this is True, the class's methods will still be checked."""
        return self._skip_class_def

    @property
    def skip_private(self):
        """If True, skip function definitions beginning with a
        single underscore and does not include them in the report."""
        return self._skip_private

    @property
    def ignore_names(self):
        """Patterns to ignore when checking documentation. Each list in `ignore_names` defines a
        different pattern to be ignored. The first element in each list is the regular expression
        for matching filenames. All remaining arguments in each list are regexes for matching names
        of functions/classes. A node is ignored if it matches the filename regex and at least one
        of the remaining regexes"""
        return self._ignore_names
