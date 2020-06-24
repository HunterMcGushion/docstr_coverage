"""Tests for :mod:`docstr_coverage.cli`"""
import os
import pytest
import re
from typing import List, Optional

from docstr_coverage.cli import collect_filepaths, do_include_filepath, parse_ignore_names_file


class Samples:
    def __init__(self, dirpath: str):
        """Convenience/helper class to organize paths to sample files

        Parameters
        ----------
        dirpath: String
            Path to a sample file subdirectory containing the required sample scripts"""
        self.dirpath = dirpath
        self.documented = os.path.join(dirpath, "documented_file.py")
        self.empty = os.path.join(dirpath, "empty_file.py")
        self.partial = os.path.join(dirpath, "partly_documented_file.py")
        self.undocumented = os.path.join(dirpath, "some_code_no_docs.py")

    @property
    def all(self) -> List[str]:
        """Get all of the sample script paths inside the subdirectory"""
        return [self.documented, self.empty, self.partial, self.undocumented]


SAMPLES_DIR = os.path.join("tests", "sample_files")
SAMPLES_A = Samples(os.path.join(SAMPLES_DIR, "subdir_a"))
SAMPLES_B = Samples(os.path.join(SAMPLES_DIR, "subdir_b"))


@pytest.fixture
def exclude_re(request) -> "re.Pattern":
    """Indirectly parametrized fixture that expects a string or None as input"""
    pattern = getattr(request, "param", None)
    return re.compile(r"{}".format(pattern)) if pattern else None


@pytest.mark.parametrize(
    ["filepath", "exclude_re", "expected"],
    [
        ("foo.js", None, False),
        ("foo.txt", None, False),
        ("foobar", None, False),
        ("foo_py.js", None, False),
        ("foo.py", None, True),
        ("foo/bar.py", None, True),
        ("foo.py", "bar", True),
        ("foo.py", "fo", False),
        ("foo.py", "foo.+\\.py", True),  # `exclude_re` requires something between "foo" and ".py"
        ("foo.py", "foo.+", False),  # ".+" applied to extension, so `filepath` is excluded
        ("foo_bar.py", "foo.+", False),
        ("foo_bar.py", "foo.+\\.py", False),
        ("foo/bar.py", "foo", False),
        ("foo/bar.py", "bar", True),
        ("foo/bar.py", ".*bar", False),
        ("foo/bar.py", "bar/", True),
        ("foo/bar/baz.py", "bar/.*", True),  # `exclude_re` starts with "bar"
        ("foo/bar/baz.py", ".*/bar/.*", False),
    ],
    indirect=["exclude_re"],
)
def test_do_include_filepath(filepath: str, exclude_re: Optional[str], expected: bool):
    """Test that :func:`docstr_coverage.cli.do_include_filepath` includes correct filepaths

    Parameters
    ----------
    filepath: String
        Filepath to match with `exclude_re`
    exclude_re: String, or None
        Pattern to check against `filepath`. Indirectly parametrized to be `re.Pattern` or None
    expected: Boolean
        Expected response to whether `filepath` should be included"""
    actual = do_include_filepath(filepath, exclude_re)
    assert actual is expected


@pytest.mark.parametrize(
    ["paths", "exclude", "expected"],
    [
        ([SAMPLES_DIR], "", SAMPLES_A.all + SAMPLES_B.all),
        ([SAMPLES_A.documented], "", [SAMPLES_A.documented]),
        ([SAMPLES_A.dirpath], "", SAMPLES_A.all),
        ([SAMPLES_A.dirpath], ".*/sample_files/.*", []),
        ([SAMPLES_A.dirpath], ".*documented_file.*", [SAMPLES_A.empty, SAMPLES_A.undocumented]),
        ([SAMPLES_A.empty, SAMPLES_A.documented], "", [SAMPLES_A.documented, SAMPLES_A.empty]),
        ([SAMPLES_A.dirpath, SAMPLES_B.dirpath], "", SAMPLES_A.all + SAMPLES_B.all),
        ([SAMPLES_A.dirpath, SAMPLES_B.dirpath], ".*subdir_a.*", SAMPLES_B.all),
        (
            [SAMPLES_A.dirpath, SAMPLES_B.documented, SAMPLES_B.empty],
            ".*subdir_a.*",
            [SAMPLES_B.documented, SAMPLES_B.empty],
        ),
        (
            [SAMPLES_A.dirpath, SAMPLES_B.dirpath],
            ".*_file\\.py",
            [SAMPLES_A.undocumented, SAMPLES_B.undocumented],
        ),
    ],
)
def test_collect_filepaths(paths: List[str], exclude: str, expected: List[str]):
    """Test that :func:`docstr_coverage.cli.collect_filepaths` includes correct filepaths

    Parameters
    ----------
    paths: List
        Path(s) to directory/file
    exclude: String
        Pattern for filepaths to exclude
    expected: List
        Expected list of filepaths to include in search"""
    actual = collect_filepaths(*paths, follow_links=False, exclude=exclude)
    assert actual == expected


@pytest.mark.parametrize(
    ["path", "expected"],
    [
        ("", ()),
        ("this_file_does_not_exist.txt", ()),
        (
            os.path.join(SAMPLES_A.dirpath, "docstr_ignore.txt"),
            (
                ["SomeFile", "method_to_ignore1", "method_to_ignore2", "method_to_ignore3"],
                ["FileWhereWeWantToIgnoreAllSpecialMethods", "__.+__"],
                [".*", "method_to_ignore_in_all_files"],
                ["a_very_important_view_file", "^get$", "^set$", "^post$"],
                ["detect_.*", "get_val.*"],
            ),
        ),
    ],
)
def test_parse_ignore_names_file(path: str, expected: tuple):
    """Test that :func:`docstr_coverage.cli.parse_ignore_names_file` correctly parses patterns

    Parameters
    ----------
    path: String
        Path to a file containing patterns to ignore
    expected: Tuple
        Expected parsed patterns from `path`"""
    actual = parse_ignore_names_file(path)
    assert actual == expected
