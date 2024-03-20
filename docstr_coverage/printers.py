"""All logic used to print a recorded ResultCollection to stdout.
Currently, this module is in BETA and its interface may change in future versions."""
import json
import logging
import os
from abc import ABC, abstractmethod
from math import floor

from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.result_collection import FileStatus, ResultCollection
from tabulate import tabulate

_GRADES = (
    ("AMAZING! Your docstrings are truly a wonder to behold!", 100),
    ("Excellent", 92),
    ("Great", 85),
    ("Very good", 70),
    ("Good", 60),
    ("Not bad", 40),
    ("Not good", 25),
    ("Extremely poor", 10),
    ("Not documented at all", 2),
    ("Do you even docstring?", 0),
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(message)s")


def print_line(line=""):
    """Prints `line`

    Parameters
    ----------
    line: String
        The text to print"""
    logger.info(line)


class Printer(ABC):
    @abstractmethod
    def print(self, results: ResultCollection):
        """Prints a provided set of results to stdout.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        raise NotImplementedError()


class LegacyPrinter(Printer):
    """Printing functionality consistent with the original early-versions docstr-coverage outputs.

    In future versions, the interface of this class will be refined and an abstract superclass
    will be extracted. Thus, coding against the current interface will require refactorings with
    future versions of docstr-coverage."""

    def __init__(self, verbosity: int, ignore_config: IgnoreConfig = IgnoreConfig()):
        self.verbosity = verbosity
        self.ignore_config = ignore_config

    def print(self, results):
        """Prints a provided set of results to stdout.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        if self.verbosity >= 2:
            self._print_file_statistics(results)
        if self.verbosity >= 1:
            self._print_overall_statistics(results)

    def _print_file_statistics(self, results):
        """Prints the file specific information to stdout.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        for file_path, file in results.files():
            if self.verbosity < 4 and file.count_aggregate().missing == 0:
                # Don't print fully documented files
                continue

            # File Header
            print_line('\nFile: "{}"'.format(file_path))

            # List of missing docstrings
            if self.verbosity >= 3:
                if file.status == FileStatus.EMPTY and self.verbosity > 3:
                    print_line(" - File is empty")
                for expected_docstr in file._expected_docstrings:
                    if expected_docstr.has_docstring and self.verbosity > 3:
                        print_line(
                            " - Found docstring for `{0}`".format(expected_docstr.node_identifier)
                        )
                    elif expected_docstr.ignore_reason and self.verbosity > 3:
                        print_line(
                            " - Ignored `{0}`: reason: `{1}`".format(
                                expected_docstr.node_identifier, expected_docstr.ignore_reason
                            )
                        )
                    elif not expected_docstr.has_docstring and not expected_docstr.ignore_reason:
                        if expected_docstr.node_identifier == "module docstring":
                            print_line(" - No module docstring")
                        else:
                            print_line(
                                " - No docstring for `{0}`".format(expected_docstr.node_identifier)
                            )

            # Statistics
            count = file.count_aggregate()
            print_line(
                " Needed: %s; Found: %s; Missing: %s; Coverage: %.1f%%"
                % (
                    count.needed,
                    count.found,
                    count.missing,
                    count.coverage(),
                ),
            )
            print_line()
        print_line()

    def _print_overall_statistics(self, results):
        """Prints overall results (aggregated over all files) to stdout.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        count = results.count_aggregate()

        postfix = ""
        if count.num_empty_files > 0:
            postfix = " (%s files are empty)" % count.num_empty_files
        if self.ignore_config.skip_magic:
            postfix += " (skipped all non-init magic methods)"
        if self.ignore_config.skip_file_docstring:
            postfix += " (skipped file-level docstrings)"
        if self.ignore_config.skip_init:
            postfix += " (skipped __init__ methods)"
        if self.ignore_config.skip_class_def:
            postfix += " (skipped class definitions)"
        if self.ignore_config.skip_private:
            postfix += " (skipped private methods)"

        if count.num_files > 1:
            print_line("Overall statistics for %s files%s:" % (count.num_files, postfix))
        else:
            print_line("Overall statistics%s:" % postfix)

        print_line(
            "Needed: {}  -  Found: {}  -  Missing: {}".format(
                count.needed, count.found, count.missing
            ),
        )

        # Calculate Total Grade
        grade = next(
            message for message, grade_threshold in _GRADES if grade_threshold <= count.coverage()
        )

        print_line("Total coverage: {:.1f}%  -  Grade: {}".format(count.coverage(), grade))


class JsonPrinter(Printer):
    def print(self, results):
        """Prints a provided set of results to stdout in format JSON.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""

        file_results, total_results = results.to_legacy()
        print(json.dumps({"files": file_results, "result": total_results}))


class GitHubCommentPrinter(Printer):
    def __init__(self, verbosity: int, fail_under: int):
        self.verbosity = verbosity
        self.fail_under = fail_under

    def print(self, results: ResultCollection):
        """Prints a provided set of results to stdout in format JSON.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        file_results, total_results = results.to_legacy()

        success = total_results["coverage"] >= self.fail_under

        print_line("## [:books: docstr_coverage](https://docstr-coverage.readthedocs.io/en/latest/api_essentials.html) status: %s **%s**" % (self._status_icon(success), self._status_text(success)))
        print_line()
        print_line("Overall coverage: **`%s%%`** (required **`%s%%`**)" % (floor(total_results["coverage"]), floor(self.fail_under)))
        print_line()

        result_table = []
        for file_path, file in results.files():
            if self.verbosity < 4 and file.count_aggregate().missing == 0:
                # Don't print fully documented files
                continue

            count = file.count_aggregate()

            row = []
            row.append("%s `%s`" % (self._status_icon(count.coverage() >= self.fail_under), os.path.relpath(file_path, start=os.curdir)))
            row += [count.needed, count.found, count.missing, "%.1f%%" % count.coverage()]

            result_table.append(row)

        print_line("<details><summary>Additional details and impacted files</summary>")
        print_line()
        print_line(tabulate(result_table, headers=["Filename", "Needed", "Found", "Missing", "Coverage"], tablefmt="pipe", colalign = ('left','right','right','right','right')))
        print_line("</details>")

    def _status_icon(self, success: bool) -> str:
        return ":white_check_mark:" if success else ":x:"

    def _status_text(self, success: bool) -> str:
        return "SUCCESS" if success else "FAILED"