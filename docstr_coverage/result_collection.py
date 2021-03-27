import enum
import functools
import operator
import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Generator, Tuple


class ResultCollection:
    def __init__(self):
        self._folders: Dict[str, "Folder"] = dict()

    def get_module(self, file_path: str):
        folder_path, file_name = os.path.split(file_path)
        folder: Folder
        try:
            folder = self._folders[folder_path]
        except KeyError:
            folder = Folder()
            self._folders[folder_path] = folder
        return folder.get_module(file_name=file_name)

    def count(self) -> "_AggregatedCount":
        counts = (folder.count() for folder in self._folders.values())
        return functools.reduce(operator.add, counts, _AggregatedCount())

    def files(self) -> Generator[Tuple[str, "File"], None, None]:
        for folder_path, folder in self._folders.items():
            for file_name, file in folder.files():
                yield "{}{}{}".format(folder_path, os.path.sep, file_name), file

    def to_legacy(self) -> Tuple[Dict, Dict]:
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


class Folder:
    def __init__(self):
        self._files: Dict[str, "File"] = dict()

    def get_module(self, file_name: str):
        try:
            return self._files[file_name]
        except KeyError:
            file = File()
            self._files[file_name] = file
            return file

    def count(self) -> "_AggregatedCount":
        counts = (file.count() for file in self._files.values())
        return functools.reduce(operator.add, counts, _AggregatedCount())

    def files(self) -> Generator[Tuple[str, "File"], None, None]:
        for name, file in self._files.items():
            yield name, file


class FileStatus(enum.Enum):
    ANALYZED = (1,)
    EMPTY = 2
    # Note: We may eventually add IGNORED here, but this will require some more refactoring


class File:
    def __init__(self) -> None:
        super().__init__()
        self._expected_docstrings: List["_ExpectedDocstring"] = []
        self._status = FileStatus.ANALYZED

    def report(self, identifier: str, has_docstring: bool, ignore_reason: Optional[str] = None):
        self._expected_docstrings.append(
            _ExpectedDocstring(
                node_identifier=identifier, has_docstring=has_docstring, ignore_reason=ignore_reason
            )
        )

    def report_module(self, has_docstring: bool, ignore_reason: Optional[str] = None):
        self.report(
            identifier="module docstring", has_docstring=has_docstring, ignore_reason=ignore_reason
        )

    def expected_docstrings(self) -> Generator["_ExpectedDocstring", None, None]:
        for exds in self._expected_docstrings:
            yield exds

    def set_file_status(self, status: FileStatus):
        self._status = status

    def count(self) -> "_FileCount":
        count = _FileCount()
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

    def get_status(self) -> FileStatus:
        return self._status


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
            return 100.0


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
            return 100.0

    def found_needed_docstr(self):
        self.needed += 1
        self.found += 1

    def missed_needed_docstring(self):
        self.needed += 1
        self.missing += 1

    def found_empty_file(self):
        self.is_empty = True
