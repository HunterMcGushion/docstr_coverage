import os

from docstr_coverage import get_docstring_coverage

SAMPLES_DIRECTORY = os.path.join("tests", "sample_files")
EMPTY_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "empty_file.py")
DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "documented_file.py")
PARTLY_DOCUMENTED_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "partly_documented_file.py")
SOME_CODE_NO_DOCS_FILE_PATH = os.path.join(SAMPLES_DIRECTORY, "some_code_no_docs.py")


def test_should_report_for_an_empty_file():
    file_results, total_results = get_docstring_coverage([EMPTY_FILE_PATH],)
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
    file_results, total_results = get_docstring_coverage([DOCUMENTED_FILE_PATH],)
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
    assert total_results == {
        "missing_count": 4,
        "needed_count": 14,
        "coverage": 71.42857142857143,
    }


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
