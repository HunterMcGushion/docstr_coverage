import enum
import functools
import operator
import os
from dataclasses import dataclass
from typing import List, Optional, Dict


class ResultCollection:
    folders: Dict[str, "Folder"] = dict()

    def get_module(self, file_path: str):
        folder_path, file_name = os.path.split(file_path)
        folder: Folder
        try:
            folder = self.folders[folder_path]
        except KeyError:
            folder = Folder()
            self.folders[folder_path] = folder
        return folder.get_module(file_name=file_name)

    def count(self) -> "_AggregatedCount":
        counts = (folder.count() for folder in self.folders.values())
        return functools.reduce(operator.add, counts, _AggregatedCount())


class Folder:
    files: Dict[str, "File"] = dict()

    def get_module(self, file_name: str):
        try:
            return self.files[file_name]
        except KeyError:
            file = File()
            self.files[file_name] = file
            return file

    def count(self) -> "_AggregatedCount":
        counts = (file.count() for file in self.files.values())
        return functools.reduce(operator.add, counts, _AggregatedCount())


class FileStatus(enum.Enum):
    ANALYZED = (1,)
    EMPTY = 2
    # Note: We may eventually add IGNORED here, but this will require some more refactoring


class File:
    expected_docstrings: List["_ExpectedDocstring"]
    status: FileStatus

    def __init__(self) -> None:
        super().__init__()
        self.expected_docstrings = []

    def report(self, identifier: str, has_docstring: bool, ignore_reason: Optional[str] = None):
        self.expected_docstrings.append(
            _ExpectedDocstring(
                node_identifier=identifier, has_docstring=has_docstring, ignore_reason=ignore_reason
            )
        )

    def report_module(self, has_docstring: bool, ignore_reason: Optional[str] = None):
        self.report(
            identifier="module docstring", has_docstring=has_docstring, ignore_reason=ignore_reason
        )

    def set_file_status(self, status: FileStatus):
        self.status = status

    def count(self) -> "_FileCount":
        count = _FileCount()
        for expd in self.expected_docstrings:
            if expd.ignore_reason:
                pass  # Ignores will be counted in a future version
            elif expd.has_docstring:
                count.found_needed_docstr()
            else:
                count.missed_needed_docstring()
        return count


@dataclass
class _ExpectedDocstring:
    node_identifier: str
    has_docstring: bool
    ignore_reason: Optional[str]


class _AggregatedCount:
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
        if isinstance(other, _AggregatedCount):
            return _AggregatedCount(
                num_files=self.num_files + other.num_files,
                num_empty_files=self.num_empty_files + other.num_empty_files,
                needed=self.needed + other.needed,
                found=self.found + other.found,
                missing=self.missing + other.missing,
            )
        elif isinstance(other, _FileCount):
            return _AggregatedCount(
                num_files=self.num_files + 1,
                num_empty_files=self.num_empty_files + int(other.is_empty),
                needed=self.needed + other.needed,
                found=self.found + other.found,
                missing=self.missing + other.missing,
            )
        else:
            # Chosen NotImplemented over TypeError as specified in
            #   https://docs.python.org/3/reference/datamodel.html#object.__add__ :
            #   "If one of those methods does not support the operation with the supplied arguments,
            #   it should return NotImplemented."
            raise NotImplementedError(
                "Can only add _Count and _AggregatedCount instances to a _AggregatedCount instance"
            )

    def coverage(self) -> float:
        try:
            return self.found * 100 / self.needed
        except ZeroDivisionError:
            return 0.0


class _FileCount:
    def __init__(self) -> None:
        super().__init__()
        self.is_empty = False
        self.needed = 0
        self.found = 0
        self.missing = 0
        # Note: In the future, we'll add `self.ignored` here

    def coverage(self) -> float:
        try:
            return self.found * 100 / self.needed
        except ZeroDivisionError:
            return 0.0

    def found_needed_docstr(self):
        self.needed += 1
        self.found += 1

    def missed_needed_docstring(self):
        self.needed += 1
        self.missing += 1

    def found_empty_file(self):
        self.is_empty = True
