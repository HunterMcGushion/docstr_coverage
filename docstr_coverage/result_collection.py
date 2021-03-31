"""Module containing the classes required to collect
 and aggregate docstring information.

Currently, this module is in BETA and its interface
 may change in future versions."""

import enum
import functools
import operator
from typing import Dict, Generator, List, Optional, Tuple


class ResultCollection:
    """A result collection contains the information about the presence
    of docstrings collected during the walk through the files.
    It thus allows to get information about missing docstrings for any
    inspected file, and to extract summary metrics (e.g. coverage)
    without having to re-walk over the files again."""

    def __init__(self):
        self._files: Dict[str, "File"] = dict()

    def get_file(self, file_path: str) -> "File":
        """
        Provides access to the docstring information for specific files.
        This primarily targets information collection phase
        (thus the docstr-coverage internal process).

        If no file with the provided name is on record yet,
         a new empty file information instance is created and returned.

        Parameters
        ----------
        file_path: String
            The path of the file for which the information is requested.

        Returns
        -------
        File
            The file (information) instance used to track docstring information.

        """
        file: File
        try:
            return self._files[file_path]
        except KeyError:
            file = File()
            self._files[file_path] = file
            return file

    def count(self) -> "AggregatedCount":
        """
        Walks through all the tracked files in this result collection,
        and counts overall statistics, such as #missing docstring.

        Returns
        -------
        AggregatedCount
            A count instance containing a range of docstring counts."""

        counts = (folder.count() for folder in self._files.values())
        return functools.reduce(operator.add, counts, AggregatedCount())

    def files(self) -> Generator[Tuple[str, "File"], None, None]:
        """Generator, allowing to iterate over all
        (file-name, file-info) tuples in this result collection."""

        for file_path, file in self._files.items():
            yield file_path, file

    def to_legacy(self) -> Tuple[Dict, Dict]:
        """Converts the information in this ResultsCollection
        into the less expressive dictionary of counts used since
        early versions of docstr-coverage."""

        file_results = dict()
        for filename, file in self.files():
            missing_list = [
                e.node_identifier
                for e in file.expected_docstrings()
                if not e.ignore_reason
                and not e.has_docstring
                and not e.node_identifier == "module docstring"
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
            count = file.count()
            file_results[filename] = {
                "missing": missing_list,
                "module_doc": has_module_doc,
                "missing_count": count.missing,
                "needed_count": count.needed,
                "coverage": count.coverage(),
                "empty": count.is_empty,
            }
        total_count = self.count()
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
        self._expected_docstrings: List["ExpectedDocstring"] = []
        self._status = FileStatus.ANALYZED

    def report(self, identifier: str, has_docstring: bool, ignore_reason: Optional[str] = None):
        """Used internally by docstr-coverage to report the status of a
        single, expected docstring.

        For module docstrings, use `report_module(...)` instead of this method.

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

    def report_module(self, has_docstring: bool, ignore_reason: Optional[str] = None):
        """Used internally by docstr-coverage to report the status of a module docstring.

        Parameters
        ----------
        has_docstring: bool
            True if and only if the docstring was present
        ignore_reason: Optional[str]
            Used to indicate that the docstring should be ignored (independent of its presence)"""

        self.report(
            identifier="module docstring", has_docstring=has_docstring, ignore_reason=ignore_reason
        )

    def expected_docstrings(self) -> Generator["ExpectedDocstring", None, None]:
        """A generator, allowing to iterate over all reported (present or missing)
        docstring presences of this file."""
        for exds in self._expected_docstrings:
            yield exds

    def set_file_status(self, status: FileStatus):
        """
        Method used internally by docstr-coverage.
        The default file status is ANALYZED. To change this (e.g. to EMPTY),
        this method has to be called.

        Parameters
        ----------
        status: FileStatus
            The status for this file to record
        """
        self._status = status

    def count(self) -> "FileCount":
        """
        Walks through all docstring reports of this file
         and counts them by state (e.g. the #missing).

        Returns
        -------
        FileCount
            A count instance containing a range of docstring counts."""

        count = FileCount()
        if self._status == FileStatus.EMPTY:
            count._found_empty_file()
        else:
            for expd in self._expected_docstrings:
                if expd.ignore_reason:
                    pass  # Ignores will be counted in a future version
                elif expd.has_docstring:
                    count._found_needed_docstr()
                else:
                    count._missed_needed_docstring()
        return count

    def get_status(self) -> FileStatus:
        return self._status


class ExpectedDocstring:
    """A data class containing information about a single docstring and its presence."""

    def __init__(
        self, node_identifier: str, has_docstring: bool, ignore_reason: Optional[str]
    ) -> None:
        super().__init__()
        self.node_identifier = node_identifier
        self.has_docstring = has_docstring
        self.ignore_reason = ignore_reason


def _calculate_coverage(found: int, needed: int) -> float:
    """
    Calculates the coverage in percent, as the ratio of #found and #needed docstrings.

    Parameters
    ----------
    found: int
        The number of found docstrings
    needed: int
        The number of needed (i.e., non-ignored) docstrings

    Returns
    -------
    float
        The coverage as percentage, i.e., in [0;100]

    """
    try:
        return found * 100 / needed
    except ZeroDivisionError:
        return 100.0


class AggregatedCount:
    """Counts of docstrings by presence, such as #missing, representing a list of files"""

    def __init__(
        self,
        num_files: int = 0,
        num_empty_files: int = 0,
        needed: int = 0,
        found: int = 0,
        missing: int = 0,
        # Note: In the future, we'll add `self.ignored` here
    ):
        self.num_files: int = num_files
        self.num_empty_files: int = num_empty_files
        self.needed: int = needed
        self.found: int = found
        self.missing: int = missing

    def __add__(self, other):
        if isinstance(other, AggregatedCount):
            return AggregatedCount(
                num_files=self.num_files + other.num_files,
                num_empty_files=self.num_empty_files + other.num_empty_files,
                needed=self.needed + other.needed,
                found=self.found + other.found,
                missing=self.missing + other.missing,
            )
        elif isinstance(other, FileCount):
            return AggregatedCount(
                num_files=self.num_files + 1,
                num_empty_files=self.num_empty_files + int(other.is_empty),
                needed=self.needed + other.needed,
                found=self.found + other.found,
                missing=self.missing + other.missing,
            )
        else:
            # Chosen NotImplementedError over TypeError as specified in
            #   https://docs.python.org/3/reference/datamodel.html#object.__add__ :
            #   "If one of those methods does not support the operation with the supplied arguments,
            #   it should return NotImplemented."
            raise NotImplementedError(
                "Can only add _Count and _AggregatedCount instances to a _AggregatedCount instance"
                " but received {}".format(type(other))
            )

    def coverage(self) -> float:
        """Calculates the coverage in percent, given the counts recorded in self.
        If no docstrings were needed, the presence is reported as 100%."""
        return _calculate_coverage(found=self.found, needed=self.needed)


class FileCount:
    """Counts of docstrings by presence, such as #missing, representing a single file"""

    def __init__(self) -> None:
        super().__init__()
        self.is_empty = False
        self.needed = 0
        self.found = 0
        self.missing = 0
        # Note: In the future, we'll add `self.ignored` here

    def coverage(self) -> float:
        """Calculates the coverage in percent, given the counts recorded in self.
        If no docstrings were needed, the presence is reported as 100%."""
        return _calculate_coverage(found=self.found, needed=self.needed)

    def _found_needed_docstr(self):
        """To be called to count a present non-ignored docstring."""
        self.needed += 1
        self.found += 1

    def _missed_needed_docstring(self):
        """To be called to count a missing non-ignored docstring."""
        self.needed += 1
        self.missing += 1

    def _found_empty_file(self):
        """To be called to count the presence of an empty file."""
        self.is_empty = True
