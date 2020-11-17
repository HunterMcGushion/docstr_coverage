import logging
import os
import pytest

from docstr_coverage import get_docstring_coverage
from docstr_coverage.coverage import GRADES

SAMPLES_DIRECTORY = os.path.join("tests", "sample_files", "subdir_a")
EMPTY_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "empty_file.py")
DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "documented_file.py")
PARTLY_DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "partly_documented_file.py")
SOME_CODE_NO_DOCS_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "some_code_no_docs.py")
PRIVATE_NO_DOCS_PATH = os.path.join(SAMPLES_DIRECTORY, "private_undocumented.py")


def test_should_report_for_an_empty_file():
    file_results, total_results = get_docstring_coverage([EMPTY_FILE_PATH])
    assert file_results == {
        EMPTY_FILE_PATH: {
            "missing": [],
            "module_doc": False,
            "missing_count": 0,
            "needed_count": 0,
            "coverage": 0,
            "empty": True,
        }
    }
    assert total_results == {"missing_count": 0, "needed_count": 0, "coverage": 100}


def test_should_report_full_coverage():
    file_results, total_results = get_docstring_coverage([DOCUMENTED_FILE_PATH])
    assert file_results == {
        DOCUMENTED_FILE_PATH: {
            "missing": [],
            "module_doc": True,
            "missing_count": 0,
            "needed_count": 9,
            "coverage": 100.0,
            "empty": False,
        }
    }
    assert total_results == {"missing_count": 0, "needed_count": 9, "coverage": 100.0}


def test_should_report_partial_coverage():
    file_results, total_results = get_docstring_coverage([PARTLY_DOCUMENTED_FILE_PATH])
    assert file_results == {
        PARTLY_DOCUMENTED_FILE_PATH: {
            "missing": ["FooBar.__init__", "foo", "bar"],
            "module_doc": False,
            "missing_count": 4,
            "needed_count": 5,
            "coverage": 20.0,
            "empty": False,
        }
    }
    assert total_results == {"missing_count": 4, "needed_count": 5, "coverage": 20.0}


def test_should_report_for_multiple_files():
    file_results, total_results = get_docstring_coverage(
        [PARTLY_DOCUMENTED_FILE_PATH, DOCUMENTED_FILE_PATH, EMPTY_FILE_PATH]
    )

    assert file_results == {
        PARTLY_DOCUMENTED_FILE_PATH: {
            "missing": ["FooBar.__init__", "foo", "bar"],
            "module_doc": False,
            "missing_count": 4,
            "needed_count": 5,
            "coverage": 20.0,
            "empty": False,
        },
        DOCUMENTED_FILE_PATH: {
            "missing": [],
            "module_doc": True,
            "missing_count": 0,
            "needed_count": 9,
            "coverage": 100.0,
            "empty": False,
        },
        EMPTY_FILE_PATH: {
            "missing": [],
            "module_doc": False,
            "missing_count": 0,
            "needed_count": 0,
            "coverage": 0,
            "empty": True,
        },
    }
    assert total_results == {"missing_count": 4, "needed_count": 14, "coverage": 71.42857142857143}


def test_should_report_when_no_docs_in_a_file():
    file_results, total_results = get_docstring_coverage([SOME_CODE_NO_DOCS_FILE_PATH])
    assert file_results == {
        SOME_CODE_NO_DOCS_FILE_PATH: {
            "missing": ["foo"],
            "module_doc": False,
            "missing_count": 2,
            "needed_count": 2,
            "coverage": 0.0,
            "empty": False,
        }
    }
    assert total_results == {"missing_count": 2, "needed_count": 2, "coverage": 0.0}


##################################################
# Logging Tests
##################################################
@pytest.mark.parametrize(
    ["expected"],
    [
        (
            [
                '\nFile: "tests/sample_files/subdir_a/empty_file.py"',
                " - File is empty",
                " Needed: 0; Found: 0; Missing: 0; Coverage: 0.0%",
                "\n",
                "Overall statistics (1 files are empty):",
                "Needed: 0  -  Found: 0  -  Missing: 0",
                "Total coverage: 100.0%  -  Grade: " + GRADES[0][0],
            ],
        )
    ],
)
def test_logging_empty_file(caplog, expected):
    with caplog.at_level(logging.DEBUG):
        _file_results, _total_results = get_docstring_coverage([EMPTY_FILE_PATH], verbose=3)

    assert caplog.messages == expected


@pytest.mark.parametrize(
    ["expected", "verbose", "ignore_names"],
    [
        (
            [
                '\nFile: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " - No module docstring",
                " - No docstring for `foo`",
                " - No docstring for `bar`",
                " Needed: 4; Found: 1; Missing: 3; Coverage: 25.0%",
                "\n",
                "Overall statistics:",
                "Needed: 4  -  Found: 1  -  Missing: 3",
                "Total coverage: 25.0%  -  Grade: " + GRADES[6][0],
            ],
            3,
            ([".*", "__.+__"],),
        ),
        (
            [
                '\nFile: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " - No module docstring",
                " - No docstring for `FooBar.__init__`",
                " - No docstring for `foo`",
                " - No docstring for `bar`",
                " Needed: 5; Found: 1; Missing: 4; Coverage: 20.0%",
                "\n",
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + GRADES[7][0],
            ],
            3,
            (),
        ),
        (
            [
                '\nFile: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " Needed: 5; Found: 1; Missing: 4; Coverage: 20.0%",
                "\n",
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + GRADES[7][0],
            ],
            2,
            (),
        ),
        (
            [
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + GRADES[7][0],
            ],
            1,
            (),
        ),
        (
            [
                "Overall statistics:",
                "Needed: 2  -  Found: 1  -  Missing: 1",
                "Total coverage: 50.0%  -  Grade: " + GRADES[5][0],
            ],
            1,
            ([".*", ".*"],),
        ),
    ],
)
def test_logging_partially_documented_file(caplog, expected, verbose, ignore_names):
    with caplog.at_level(logging.DEBUG):
        _file_results, _total_results = get_docstring_coverage(
            [PARTLY_DOCUMENTED_FILE_PATH], verbose=verbose, ignore_names=ignore_names
        )

    assert caplog.messages == expected


def test_skip_private():
    file_results, total_results = get_docstring_coverage([PRIVATE_NO_DOCS_PATH], skip_private=True)
    assert file_results[PRIVATE_NO_DOCS_PATH] == {
        "missing": ["__dunder", "__trunder", "____quadrunder"],
        "module_doc": False,
        "missing_count": 3,
        "needed_count": 4,
        "coverage": 25.0,
        "empty": False,
    }
    assert total_results == {"missing_count": 3, "needed_count": 4, "coverage": 25.0}
