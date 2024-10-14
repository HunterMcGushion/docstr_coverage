import logging
import os
import platform

import pytest

from docstr_coverage import analyze
from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.printers import _GRADES, LegacyPrinter, MarkdownPrinter

SAMPLES_DIRECTORY = os.path.join("tests", "sample_files", "subdir_a")
EMPTY_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "empty_file.py")
DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "documented_file.py")
PARTLY_DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "partly_documented_file.py")
SOME_CODE_NO_DOCS_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "some_code_no_docs.py")

EXCUSED_SAMPLES_DIRECTORY = os.path.join("tests", "excused_samples")
FULLY_EXCUSED_FILE_PATH = os.path.join(EXCUSED_SAMPLES_DIRECTORY, "fully_excused.py")
PARTLY_EXCUSED_FILE_PATH = os.path.join(EXCUSED_SAMPLES_DIRECTORY, "partially_excused.py")

SAMPLES_C_DIRECTORY = os.path.join("tests", "extra_samples")
PRIVATE_NO_DOCS_PATH = os.path.join(SAMPLES_C_DIRECTORY, "private_undocumented.py")

INDIVIDUAL_SAMPLES_DIR = os.path.join("tests", "individual_samples")


def test_should_report_for_an_empty_file():
    result = analyze([EMPTY_FILE_PATH])
    file_results, total_results = result.to_legacy()
    assert file_results == {
        EMPTY_FILE_PATH: {
            "missing": [],
            "module_doc": False,
            "missing_count": 0,
            "needed_count": 0,
            "coverage": 100.0,
            "empty": True,
        }
    }
    assert total_results == {"missing_count": 0, "needed_count": 0, "coverage": 100}


@pytest.mark.parametrize(
    ["file_path", "needed_count"], [(DOCUMENTED_FILE_PATH, 11), (FULLY_EXCUSED_FILE_PATH, 10)]
)
def test_should_report_full_coverage(file_path, needed_count):
    result = analyze([file_path])
    file_results, total_results = result.to_legacy()
    assert file_results == {
        file_path: {
            "missing": [],
            "module_doc": True,
            "missing_count": 0,
            "needed_count": needed_count,
            "coverage": 100.0,
            "empty": False,
        }
    }
    assert total_results == {"missing_count": 0, "needed_count": needed_count, "coverage": 100.0}


@pytest.mark.parametrize(
    ["file_path", "missing", "module_doc", "missing_count", "needed_count", "coverage"],
    [
        (PARTLY_DOCUMENTED_FILE_PATH, ["FooBar.__init__", "foo", "bar"], False, 4, 5, 20.0),
        (PARTLY_EXCUSED_FILE_PATH, ["FooBar.__init__", "bar"], True, 2, 8, 75.0),
    ],
)
def test_should_report_partial_coverage(
    file_path, missing, module_doc, missing_count, needed_count, coverage
):
    result = analyze([file_path])
    file_results, total_results = result.to_legacy()
    assert file_results == {
        file_path: {
            "missing": missing,
            "module_doc": module_doc,
            "missing_count": missing_count,
            "needed_count": needed_count,
            "coverage": coverage,
            "empty": False,
        }
    }
    assert total_results == {
        "missing_count": missing_count,
        "needed_count": needed_count,
        "coverage": coverage,
    }


def test_should_report_for_multiple_files():
    result = analyze([PARTLY_DOCUMENTED_FILE_PATH, DOCUMENTED_FILE_PATH, EMPTY_FILE_PATH])
    file_results, total_results = result.to_legacy()

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
            "needed_count": 11,
            "coverage": 100.0,
            "empty": False,
        },
        EMPTY_FILE_PATH: {
            "missing": [],
            "module_doc": False,
            "missing_count": 0,
            "needed_count": 0,
            "coverage": 100.0,
            "empty": True,
        },
    }
    assert total_results == {"missing_count": 4, "needed_count": 16, "coverage": 75.0}


def test_should_report_when_no_docs_in_a_file():
    result = analyze([SOME_CODE_NO_DOCS_FILE_PATH])
    file_results, total_results = result.to_legacy()
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
                "",
                'File: "tests/sample_files/subdir_a/empty_file.py"',
                " - File is empty",
                " Needed: 0; Found: 0; Missing: 0; Coverage: 100.0%",
                "",
                "",
                "Overall statistics (1 files are empty):",
                "Needed: 0  -  Found: 0  -  Missing: 0",
                "Total coverage: 100.0%  -  Grade: " + _GRADES[0][0],
            ],
        )
    ],
)
def test_legacy_printer_logging_empty_file(caplog, expected):
    with caplog.at_level(logging.DEBUG):
        result = analyze([EMPTY_FILE_PATH])
        LegacyPrinter(result, verbosity=4).print_to_stdout()
        _file_results, _total_results = result.to_legacy()

    if platform.system() == "Windows":
        assert [m.replace("\\", "/") for m in caplog.messages] == expected
    else:
        assert caplog.messages == expected


@pytest.mark.parametrize(
    ["expected"],
    [
        (
            [
                "\n",
                'File: "tests/sample_files/subdir_a/empty_file.py"\n',
                " - File is empty\n",
                " Needed: 0; Found: 0; Missing: 0; Coverage: 100.0%\n",
                "\n",
                "\n",
                "Overall statistics (1 files are empty):\n",
                "Needed: 0  -  Found: 0  -  Missing: 0\n",
                "Total coverage: 100.0%  -  Grade: " + _GRADES[0][0],
            ],
        )
    ],
)
def test_legacy_save_to_file_printer_empty_file(tmpdir, expected):
    path = tmpdir.join("coverage-result.txt")
    result = analyze([EMPTY_FILE_PATH])
    LegacyPrinter(result, verbosity=4).save_to_file(path.strpath)

    assert path.readlines() == expected


@pytest.mark.parametrize(
    ["expected"],
    [
        (
            [
                "**File**: `tests/sample_files/subdir_a/empty_file.py`",
                "- File is empty",
                "",
                "| Needed | Found | Missing | Coverage |",
                "|---|---|---|---|",
                "| 0 | 0 | 0 | 100.0% |",
                "",
                "",
                "## Overall statistics",
                "",
                "Total coverage: **100.0%**",
                "",
                "Grade: **" + _GRADES[0][0] + "**",
                "- 1 files are empty",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 0 | 0 | 0 |",
            ],
        )
    ],
)
def test_markdown_printer_logging_empty_file(caplog, expected):
    with caplog.at_level(logging.DEBUG):
        result = analyze([EMPTY_FILE_PATH])
        MarkdownPrinter(result, verbosity=4).print_to_stdout()
        _file_results, _total_results = result.to_legacy()

    if platform.system() == "Windows":
        assert [m.replace("\\", "/") for m in caplog.messages] == expected
    else:
        assert caplog.messages == expected


@pytest.mark.parametrize(
    ["expected"],
    [
        (
            [
                "**File**: `tests/sample_files/subdir_a/empty_file.py`\n",
                "- File is empty\n",
                "\n",
                "| Needed | Found | Missing | Coverage |\n",
                "|---|---|---|---|\n",
                "| 0 | 0 | 0 | 100.0% |\n",
                "\n",
                "\n",
                "## Overall statistics\n",
                "\n",
                "Total coverage: **100.0%**\n",
                "\n",
                "Grade: **" + _GRADES[0][0] + "**\n",
                "- 1 files are empty\n",
                "\n",
                "| Needed | Found | Missing |\n",
                "|---|---|---|\n",
                "| 0 | 0 | 0 |",
            ],
        )
    ],
)
def test_markdown_save_to_file_printer_empty_file(tmpdir, expected):
    path = tmpdir.join("coverage-result.md")
    result = analyze([EMPTY_FILE_PATH])
    MarkdownPrinter(result, verbosity=4).save_to_file(path.strpath)

    assert path.readlines() == expected


@pytest.mark.parametrize(
    ["expected", "verbose", "ignore_names"],
    [
        (
            [
                "",
                'File: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " - No module docstring",
                " - No docstring for `foo`",
                " - No docstring for `bar`",
                " Needed: 4; Found: 1; Missing: 3; Coverage: 25.0%",
                "",
                "",
                "Overall statistics:",
                "Needed: 4  -  Found: 1  -  Missing: 3",
                "Total coverage: 25.0%  -  Grade: " + _GRADES[6][0],
            ],
            3,
            ([".*", "__.+__"],),
        ),
        (
            [
                "",
                'File: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " - No module docstring",
                " - No docstring for `FooBar.__init__`",
                " - No docstring for `foo`",
                " - No docstring for `bar`",
                " Needed: 5; Found: 1; Missing: 4; Coverage: 20.0%",
                "",
                "",
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + _GRADES[7][0],
            ],
            3,
            (),
        ),
        (
            [
                "",
                'File: "tests/sample_files/subdir_a/partly_documented_file.py"',
                " Needed: 5; Found: 1; Missing: 4; Coverage: 20.0%",
                "",
                "",
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + _GRADES[7][0],
            ],
            2,
            (),
        ),
        (
            [
                "Overall statistics:",
                "Needed: 5  -  Found: 1  -  Missing: 4",
                "Total coverage: 20.0%  -  Grade: " + _GRADES[7][0],
            ],
            1,
            (),
        ),
        (
            [
                "Overall statistics:",
                "Needed: 1  -  Found: 0  -  Missing: 1",
                "Total coverage: 0.0%  -  Grade: " + _GRADES[9][0],
            ],
            1,
            ([".*", ".*"],),  # ignore all, except module
        ),
    ],
)
def test_legacy_printer_logging_partially_documented_file(caplog, expected, verbose, ignore_names):
    ignore_config = IgnoreConfig(ignore_names=ignore_names)
    with caplog.at_level(logging.DEBUG):
        result = analyze([PARTLY_DOCUMENTED_FILE_PATH], ignore_config=ignore_config)
        LegacyPrinter(result, verbosity=verbose, ignore_config=ignore_config).print_to_stdout()

    if platform.system() == "Windows":
        assert [m.replace("\\", "/") for m in caplog.messages] == expected
    else:
        assert caplog.messages == expected


@pytest.mark.parametrize(
    ["expected", "verbose", "ignore_names"],
    [
        (
            [
                "**File**: `tests/sample_files/subdir_a/partly_documented_file.py`",
                "- No module docstring",
                "- No docstring for `foo`",
                "- No docstring for `bar`",
                "",
                "| Needed | Found | Missing | Coverage |",
                "|---|---|---|---|",
                "| 4 | 1 | 3 | 25.0% |",
                "",
                "",
                "## Overall statistics",
                "",
                "Total coverage: **25.0%**",
                "",
                "Grade: **" + _GRADES[6][0] + "**",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 4 | 1 | 3 |",
            ],
            3,
            ([".*", "__.+__"],),
        ),
        (
            [
                "**File**: `tests/sample_files/subdir_a/partly_documented_file.py`",
                "- No module docstring",
                "- No docstring for `FooBar.__init__`",
                "- No docstring for `foo`",
                "- No docstring for `bar`",
                "",
                "| Needed | Found | Missing | Coverage |",
                "|---|---|---|---|",
                "| 5 | 1 | 4 | 20.0% |",
                "",
                "",
                "## Overall statistics",
                "",
                "Total coverage: **20.0%**",
                "",
                "Grade: **" + _GRADES[7][0] + "**",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 5 | 1 | 4 |",
            ],
            3,
            (),
        ),
        (
            [
                "**File**: `tests/sample_files/subdir_a/partly_documented_file.py`",
                "",
                "| Needed | Found | Missing | Coverage |",
                "|---|---|---|---|",
                "| 5 | 1 | 4 | 20.0% |",
                "",
                "",
                "## Overall statistics",
                "",
                "Total coverage: **20.0%**",
                "",
                "Grade: **" + _GRADES[7][0] + "**",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 5 | 1 | 4 |",
            ],
            2,
            (),
        ),
        (
            [
                "## Overall statistics",
                "",
                "Total coverage: **20.0%**",
                "",
                "Grade: **" + _GRADES[7][0] + "**",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 5 | 1 | 4 |",
            ],
            1,
            (),
        ),
        (
            [
                "## Overall statistics",
                "",
                "Total coverage: **0.0%**",
                "",
                "Grade: **" + _GRADES[9][0] + "**",
                "",
                "| Needed | Found | Missing |",
                "|---|---|---|",
                "| 1 | 0 | 1 |",
            ],
            1,
            ([".*", ".*"],),  # ignore all, except module
        ),
    ],
)
def test_markdown_printer_logging_partially_documented_file(
    caplog, expected, verbose, ignore_names
):
    ignore_config = IgnoreConfig(ignore_names=ignore_names)
    with caplog.at_level(logging.DEBUG):
        result = analyze([PARTLY_DOCUMENTED_FILE_PATH], ignore_config=ignore_config)
        MarkdownPrinter(result, verbosity=verbose, ignore_config=ignore_config).print_to_stdout()

    if platform.system() == "Windows":
        assert [m.replace("\\", "/") for m in caplog.messages] == expected
    else:
        assert caplog.messages == expected


def test_skip_private():
    ignore_config = IgnoreConfig(skip_private=True)
    result = analyze([PRIVATE_NO_DOCS_PATH], ignore_config=ignore_config)
    file_results, total_results = result.to_legacy()
    assert file_results[PRIVATE_NO_DOCS_PATH] == {
        "missing": ["__dunder", "__adunder"],
        "module_doc": True,
        "missing_count": 2,
        "needed_count": 3,
        "coverage": 33.333333333333336,
        "empty": False,
    }
    assert total_results == {"missing_count": 2, "needed_count": 3, "coverage": 33.333333333333336}


def test_long_doc():
    """Regression test on issue 79.

    Multiline docstrings can be a smoke test when checking
    the tokenize tokens (which is based on line numbers)."""
    result = analyze([os.path.join(INDIVIDUAL_SAMPLES_DIR, "long_doc.py")])
    assert result.count_aggregate().coverage() == 75.0
    assert result.count_aggregate().num_files == 1
    # 2 + 1 inline ignore
    assert result.count_aggregate().found == 3
    assert result.count_aggregate().needed == 4


@pytest.mark.parametrize(
    ["ignore_setter", "ignore_deleter", "ignore_property", "coverage"],
    [
        (False, False, False, 3 / 6),
        (True, False, False, 3 / 5),
        (False, True, False, 3 / 5),
        (False, False, True, 3 / 5),
        (True, True, True, 3 / 3),
    ],
)
def test_skip_decorators(ignore_setter, ignore_deleter, ignore_property, coverage):
    """Tests ignoring of property decorators"""
    ignore_config = IgnoreConfig(
        skip_setter=ignore_setter,
        skip_property=ignore_property,
        skip_deleter=ignore_deleter,
    )
    result = analyze([os.path.join(INDIVIDUAL_SAMPLES_DIR, "decorators.py")], ignore_config)
    assert result.count_aggregate().coverage() == coverage * 100
