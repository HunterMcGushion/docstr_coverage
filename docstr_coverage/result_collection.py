import enum
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


class Folder:
    files: Dict[str, "File"] = dict()

    def get_module(self, file_name: str):
        try:
            return self.files[file_name]
        except KeyError:
            file = File()
            self.files[file_name] = file
            return file


class FileStatus(enum.Enum):
    ANALYZED = (1,)
    EMPTY = 2
    # Note: We may eventually add IGNORED here, but this will require some more refactoring


class File:
    expected_docstrings: List["_ExpectedDocstring"] = []
    status: FileStatus

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


@dataclass
class _ExpectedDocstring:
    node_identifier: str
    has_docstring: bool
    ignore_reason: Optional[str]
