"""Tests for :mod:`docstr_coverage.cli`"""
import os
import pytest
import re
from typing import List, Optional

from docstr_coverage.cli import collect_filepaths, do_include_filepath, parse_ignore_names_file

SAMPLES_DIRECTORY = os.path.join("tests", "sample_files")
EMPTY_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "empty_file.py")
DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "documented_file.py")
PARTLY_DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "partly_documented_file.py")
SOME_CODE_NO_DOCS_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "some_code_no_docs.py")
ALL_SAMPLE_FILE_PATHS = [
    DOCUMENTED_FILE_PATH,
    EMPTY_FILE_PATH,
    PARTLY_DOCUMENTED_FILE_PATH,
    SOME_CODE_NO_DOCS_FILE_PATH,
]


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
    ["path", "exclude", "expected"],
    [
        (DOCUMENTED_FILE_PATH, "", [DOCUMENTED_FILE_PATH]),
        (SAMPLES_DIRECTORY, "", ALL_SAMPLE_FILE_PATHS),
        (SAMPLES_DIRECTORY, ".*/sample_files/.*", []),
        (SAMPLES_DIRECTORY, ".*documented_file.*", [EMPTY_FILE_PATH, SOME_CODE_NO_DOCS_FILE_PATH]),
    ],
)
def test_collect_filepaths(path: str, exclude: str, expected: List[str]):
    """Test that :func:`docstr_coverage.cli.collect_filepaths` includes correct filepaths

    Parameters
    ----------
    path: String
        Path to directory/file
    exclude: String
        Pattern for filepaths to exclude
    expected: List
        Expected list of filepaths to include in search"""
    actual = collect_filepaths(path, follow_links=False, exclude=exclude)
    assert actual == expected


@pytest.mark.parametrize(
    ["path", "expected"],
    [
        ("", ()),
        ("this_file_does_not_exist.txt", ()),
        (
            os.path.join(SAMPLES_DIRECTORY, "docstr_ignore.txt"),
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
