"""The result_collection is a very simple module and
consists mostly on data-classes with little logic.
Thus, the tests implemented here are mostly trivial
and act primarily as smoke- and regression tests."""
import os
from typing import Dict

import pytest

from docstr_coverage.result_collection import (
    AggregatedCount,
    File,
    FileCount,
    FileStatus,
    ResultCollection,
)


def _path(*argv):
    """Creates test file paths from provided splits (folder and file names) with the
    current os file path separator."""
    return os.path.sep.join(argv)


class TestResultCollection:
    """Tests the method in the ResultCollection class"""

    def test_get_file(self):
        """Makes sure files are created and stored correctly,
        and no duplicates are created."""
        result_collection = ResultCollection()
        file_1 = result_collection.get_file(_path("some", "path", "file.py"))
        file_2 = result_collection.get_file(_path("some", "path", "file.py"))
        file_3 = result_collection.get_file(_path("some", "other", "file.py"))
        assert file_1 == file_2
        assert file_1 != file_3

    def test_to_legacy(self):
        """Some sanity checks on the conversion of ResultCollections to the legacy result format."""
        result_collection = ResultCollection()
        file_1 = result_collection.get_file(_path("my", "file.py"))
        file_1.report_module(False)
        file_1.report("method_x", True)
        file_1.report("method_y", True)
        file_2 = result_collection.get_file(_path("my", "other", "file.py"))
        file_2.report_module(False)
        file_2.report("method_x", True)
        file_2.report("method_y", True, "ignored")
        legacy_file_results, legacy_results = result_collection.to_legacy()
        assert isinstance(legacy_file_results, Dict)
        assert (
            legacy_file_results[_path("my", "file.py")]["missing"] == []
        )  # legacy does not list module docs
        assert legacy_file_results[_path("my", "file.py")]["missing_count"] == 1
        assert legacy_file_results[_path("my", "file.py")]["module_doc"] is False

        assert isinstance(legacy_results, Dict)
        assert legacy_results["missing_count"] == 2
        assert legacy_results["needed_count"] == 5
        assert legacy_results["coverage"] == 3 / 5 * 100


class TestFile:
    """Tests the method in the File class"""

    def test_count_and_iter(self):
        """Test that the iterator of expected
         (i.e., found or missing) docstrings is working,
         and that the counting works as expected
         (e.g., that it does not count ignored docstrings)."""
        file = File()
        file.report_module(False)
        file.report("method_one", True, "ignored_nonetheless")
        file.report("method_two", False, "ignored")
        file.report("method_three", False)
        file.report("Class.method", True)

        expected_docstrings = [d for d in file.expected_docstrings()]
        assert len(expected_docstrings) == 5
        count = file.count()
        assert count.is_empty is False
        assert count.found == 1
        assert count.missing == 2
        assert count.needed == 3

    def test_set_get_status(self):
        """default settings and getter / setter of status"""
        file = File()
        assert file.get_status() == FileStatus.ANALYZED
        file.set_file_status(FileStatus.EMPTY)
        assert file.get_status() == FileStatus.EMPTY

    @pytest.mark.parametrize(
        ["has_docstr", "ignore_reason"],
        [(True, None), (True, "excuse"), (False, None), (False, "excuse")],
    )
    def test_report_module(self, has_docstr, ignore_reason):
        """Tests that 'module' docstrings are recoded correctly."""
        file = File()
        file.report_module(has_docstring=has_docstr, ignore_reason=ignore_reason)
        all_docstrings = [d for d in file.expected_docstrings()]
        assert len(all_docstrings) == 1
        assert all_docstrings[0].node_identifier == "module docstring"
        assert all_docstrings[0].has_docstring is has_docstr
        assert all_docstrings[0].ignore_reason is ignore_reason

    @pytest.mark.parametrize(
        ["node_identifier", "has_docstr", "ignore_reason"],
        [
            ("abc", True, None),
            ("abc.def", True, "excuse"),
            ("abc.Adc", False, None),
            ("asd_fsa", False, "excuse"),
        ],
    )
    def test_report_(self, node_identifier, has_docstr, ignore_reason):
        """Tests that 'non-module' docstrings are recoded correctly."""
        file = File()
        file.report(
            identifier=node_identifier, has_docstring=has_docstr, ignore_reason=ignore_reason
        )
        all_docstrings = [d for d in file.expected_docstrings()]
        assert len(all_docstrings) == 1
        assert all_docstrings[0].node_identifier == node_identifier
        assert all_docstrings[0].has_docstring is has_docstr
        assert all_docstrings[0].ignore_reason is ignore_reason


class TestAggregateCount:
    """Test class for the AggregatedCount Utility class"""

    @pytest.mark.parametrize(
        ["left", "right", "expected"],
        [
            (
                AggregatedCount(num_files=0, num_empty_files=0, needed=0, found=0, missing=0),
                AggregatedCount(num_files=0, num_empty_files=0, needed=0, found=0, missing=0),
                AggregatedCount(num_files=0, num_empty_files=0, needed=0, found=0, missing=0),
            ),
            (
                AggregatedCount(num_files=1, num_empty_files=3, needed=5, found=4, missing=1),
                AggregatedCount(num_files=2, num_empty_files=4, needed=3, found=2, missing=1),
                AggregatedCount(num_files=3, num_empty_files=7, needed=8, found=6, missing=2),
            ),
        ],
    )
    def test_add(self, left, right, expected):
        """Verifies the addition and the equal operator adds/compares all fields."""
        assert left + right == expected
        # Sanity check of equals function
        other_count = AggregatedCount(
            num_files=111, num_empty_files=5, needed=123, found=123, missing=0
        )
        assert left + right != other_count

    @pytest.mark.parametrize(
        ["agg_count", "coverage"],
        [
            (AggregatedCount(num_files=0, num_empty_files=0, needed=0, found=0, missing=0), 100.0),
            (
                AggregatedCount(num_files=1, num_empty_files=3, needed=5, found=4, missing=1),
                4 / 5 * 100,
            ),
            (AggregatedCount(num_files=1, num_empty_files=3, needed=5, found=5, missing=0), 100.0),
            (AggregatedCount(num_files=1, num_empty_files=3, needed=5, found=0, missing=5), 0.0),
        ],
    )
    def test_coverage_calculation(self, agg_count, coverage):
        assert agg_count.coverage() == coverage


class TestFileCount:
    """Test class for the FileCount Utility class."""

    def test_counter_empty(self):
        """Makes sure empty files are correctly tracked"""
        counter = FileCount()
        assert (
            counter.needed == 0
            and counter.missing == 0
            and counter.found == 0
            and counter.is_empty is False
        )
        counter._found_empty_file()
        assert (
            counter.needed == 0
            and counter.missing == 0
            and counter.found == 0
            and counter.is_empty is True
        )

    def test_counter_counts(self):
        """Makes sure the counting of 'found' and 'missing' docstrings works."""
        counter = FileCount()
        assert (
            counter.needed == 0
            and counter.missing == 0
            and counter.found == 0
            and counter.is_empty is False
        )
        counter._found_needed_docstr()
        counter._found_needed_docstr()
        assert (
            counter.needed == 2
            and counter.missing == 0
            and counter.found == 2
            and counter.is_empty is False
        )
        counter._missed_needed_docstring()
        assert (
            counter.needed == 3
            and counter.missing == 1
            and counter.found == 2
            and counter.is_empty is False
        )
