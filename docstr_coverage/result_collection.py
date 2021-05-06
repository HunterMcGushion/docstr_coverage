"""Module containing the classes required to collect and aggregate docstring information.

Currently, this module is in BETA and its interface may change in future versions."""
import abc
import enum
import functools
import operator
from typing import Optional


class ResultCollection:
    """A result collection contains information about the presence of docstrings collected during
    the walk through the files. From the `ResultCollection`, information about missing docstrings
    for inspected files can be retrieved, and summary metrics (e.g. coverage) can be extracted
    without having to walk over the files again."""

    def __init__(self):
        self._files = dict()

    def get_file(self, file_path):
        """Provides access to the docstring information for specific files.
        This primarily targets information collection phase
        (thus the docstr-coverage internal process).

        If no file with the provided name is on record yet, a new empty `File` information instance
        is created and returned.

        Parameters
        ----------
        file_path: String
            The path of the file for which the information is requested.

        Returns
        -------
        File
            The file (information) instance used to track docstring information"""
        try:
            return self._files[file_path]
        except KeyError:
            file = File()
            self._files[file_path] = file
            return file

    def count_aggregate(self):
        """Walks through all the tracked files in this result collection, and counts overall
        statistics, such as #missing docstring.

        Returns
        -------
        AggregatedCount
            A count instance containing a range of docstring counts."""
        counts = (file.count_aggregate() for file in self._files.values())
        return functools.reduce(operator.add, counts, AggregatedCount())

    def files(self):
        """View of all (file-name, file-info) tuples in this result collection"""
        return self._files.items()

    def to_legacy(self):
        """Converts the information in this `ResultCollection` into the less expressive dictionary
        of counts used since the early versions of docstr-coverage.

        Returns
        -------
        Dict
            Links filename keys to a dict of stats for that filename. Example:

            >>> {
            ...     '<filename>': {
            ...         'missing': ['<method_or_class_name>', '...'],
            ...         'module_doc': '<Boolean>',
            ...         'missing_count': '<missing_count int>',
            ...         'needed_count': '<needed_docstrings_count int>',
            ...         'coverage': '<percent_of_coverage float>',
            ...         'empty': '<Boolean>'
            ...     }, ...
            ... }
        Dict
            Total summary stats for all files analyzed. Example:

            >>> {
            ...     'missing_count': '<total_missing_count int>',
            ...     'needed_count': '<total_needed_docstrings_count int>',
            ...     'coverage': '<total_percent_of_coverage float>'
            ... }
        """

        file_results = dict()
        for file_path, file in self.files():
            missing_list = [
                e.node_identifier
                for e in file.expected_docstrings()
                if not (
                    e.ignore_reason or e.has_docstring or e.node_identifier == "module docstring"
                )
            ]
            has_module_doc = (
                len(
                    [
                        e
                        for e in file.expected_docstrings()
                        if e.node_identifier == "module docstring" and e.has_docstring
                    ]
                )
                > 0
            )
            count = file.count_aggregate()
            file_results[file_path] = {
                "missing": missing_list,
                "module_doc": has_module_doc,
                "missing_count": count.missing,
                "needed_count": count.needed,
                "coverage": count.coverage(),
                "empty": count.is_empty,
            }
        total_count = self.count_aggregate()
        total_results = {
            "missing_count": total_count.missing,
            "needed_count": total_count.needed,
            "coverage": total_count.coverage(),
        }
        return file_results, total_results


class FileStatus(enum.Enum):
    """Upon inspection by docstr-coverage,
    every file is assigned exactly one of the states from this enum."""

    ANALYZED = (1,)
    EMPTY = 2
    # Note: We may eventually add IGNORED here, but this will require some more refactoring


class File:
    """The information about docstrings for a single file."""

    def __init__(self) -> None:
        super().__init__()
        self._expected_docstrings = []
        self._status = FileStatus.ANALYZED

    def collect_docstring(self, identifier: str, has_docstring: bool, ignore_reason: str = None):
        """Used internally by docstr-coverage to collect the status of a single, expected docstring.

        For module docstrings, use `collect_module_docstring(...)` instead of this method.

        Parameters
        ----------
        identifier: String
            The identifier of the docstring (typically qualified function/class name)
        has_docstring: bool
            True if and only if the docstring was present
        ignore_reason: Optional[str]
            Used to indicate that the docstring should be ignored (independent of its presence)"""
        self._expected_docstrings.append(
            ExpectedDocstring(
                node_identifier=identifier, has_docstring=has_docstring, ignore_reason=ignore_reason
            )
        )

    def collect_module_docstring(self, has_docstring: bool, ignore_reason: str = None):
        """Used internally by docstr-coverage to collect the status of a module docstring.

        Parameters
        ----------
        has_docstring: bool
            True if and only if the docstring was present
        ignore_reason: Optional[str]
            Used to indicate that the docstring should be ignored (independent of its presence)"""
        self.collect_docstring(
            identifier="module docstring", has_docstring=has_docstring, ignore_reason=ignore_reason
        )

    def expected_docstrings(self):
        """A generator, iterating over all reported (present or missing) docstrings in this file"""
        return iter(self._expected_docstrings)

    @property
    def status(self) -> FileStatus:
        return self._status

    @status.setter
    def status(self, status):
        """Method used internally by docstr-coverage.
        The default file status is ANALYZED. To change this (e.g. to EMPTY),
        this method has to be called.

        Parameters
        ----------
        status: FileStatus
            The status for this file to record"""
        self._status = status

    def count_aggregate(self):
        """Walks through all docstring reports of this file and counts them by state
        (e.g. the #missing).

        Returns
        -------
        FileCount
            A count instance containing a range of docstring counts."""
        count = FileCount()
        if self._status == FileStatus.EMPTY:
            count.found_empty_file()
        else:
            for expd in self._expected_docstrings:
                if expd.ignore_reason:
                    pass  # Ignores will be counted in a future version
                elif expd.has_docstring:
                    count.found_needed_docstr()
                else:
                    count.missed_needed_docstring()
        return count


class ExpectedDocstring:
    """A class containing information about a single docstring and its presence"""

    def __init__(
        self, node_identifier: str, has_docstring: bool, ignore_reason: Optional[str]
    ) -> None:
        super().__init__()
        self.node_identifier = node_identifier
        self.has_docstring = has_docstring
        self.ignore_reason = ignore_reason


class _DocstrCount(abc.ABC):
    """ABSTRACT superclass of classes used to count docstrings by presence.
    See subclasses `AggregatedCount` and `FileCount`.

    Do not directly create instances of this abstract superclass (even though
    it has no abstract methods)."""

    def __init__(self, needed: int, found: int, missing: int):
        # Note: In the future, we'll add `self.ignored` here
        self.needed = needed
        self.found = found
        self.missing = missing

    def coverage(self):
        """Calculates the coverage in percent, given the counts recorded in self.
        If no docstrings were needed, the presence is reported as 100%."""
        try:
            return self.found * 100 / self.needed
        except ZeroDivisionError:
            return 100.0


class AggregatedCount(_DocstrCount):
    """Counts of docstrings by presence, such as #missing, representing a list of files"""

    def __init__(
        self,
        num_files: int = 0,
        num_empty_files: int = 0,
        needed: int = 0,
        found: int = 0,
        missing: int = 0,
    ):
        super().__init__(needed=needed, found=found, missing=missing)
        self.num_files = num_files
        self.num_empty_files = num_empty_files

    def __add__(self, other):
        if isinstance(other, _DocstrCount):
            aggregated = AggregatedCount(
                needed=self.needed + other.needed,
                found=self.found + other.found,
                missing=self.missing + other.missing,
            )
            if isinstance(other, AggregatedCount):
                aggregated.num_files = self.num_files + other.num_files
                aggregated.num_empty_files = self.num_empty_files + other.num_empty_files
            elif isinstance(other, FileCount):
                aggregated.num_files = self.num_files + 1
                aggregated.num_empty_files = self.num_empty_files + int(other.is_empty)
            else:
                raise NotImplementedError(
                    "Received unexpected DocstrCount subtype ({}). "
                    "Please report to docstr-coverage issue tracker.".format(type(other))
                )
            return aggregated
        else:
            # Chosen NotImplementedError over TypeError as specified in
            #   https://docs.python.org/3/reference/datamodel.html#object.__add__ :
            #   "If one of those methods does not support the operation with the supplied arguments,
            #   it should return NotImplemented."
            raise NotImplementedError(
                "Can only add _Count and _AggregatedCount instances to a _AggregatedCount instance"
                " but received {}".format(type(other))
            )

    def __eq__(self, other):
        if isinstance(other, AggregatedCount):
            return (
                self.num_files == other.num_files
                and self.num_empty_files == other.num_empty_files
                and self.needed == other.needed
                and self.found == other.found
                and self.missing == other.missing
            )
        return False


class FileCount(_DocstrCount):
    """Counts of docstrings by presence, such as #missing, representing a single file"""

    def __init__(self) -> None:
        super().__init__(needed=0, found=0, missing=0)
        self.is_empty = False

    def found_needed_docstr(self):
        """To be called to count a present non-ignored docstring."""
        self.needed += 1
        self.found += 1

    def missed_needed_docstring(self):
        """To be called to count a missing non-ignored docstring."""
        self.needed += 1
        self.missing += 1

    def found_empty_file(self):
        """To be called to count the presence of an empty file."""
        self.is_empty = True
