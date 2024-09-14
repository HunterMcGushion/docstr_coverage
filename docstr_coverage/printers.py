"""All logic used to print a recorded ResultCollection to stdout.
Currently, this module is in BETA and its interface may change in future versions."""
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod

from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.result_collection import FileStatus, ResultCollection

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


# TODO: 1st - collect data in structure; 2nd - print (with selected printer) info


@dataclass(frozen=True)
class IgnoredNode:
    """Data Structure for nodes that was ignored in checking."""
    identifier: str
    reason: str


@dataclass(frozen=True)
class FileCoverageStat:
    """Data Structure of coverage info about one file."""
    path: str
    is_empty: bool
    nodes_with_docstring: tuple[str, ...]
    nodes_without_docstring: tuple[str, ...]
    ignored_nodes: tuple[IgnoredNode, ...]
    needed: int
    found: int
    missing: int
    coverage: float


@dataclass(frozen=True)
class OverallCoverageStat:
    """Data Structure of coverage statistic"""
    num_empty_files: int
    num_files: int
    is_skip_magic: bool
    is_skip_file_docstring: bool
    is_skip_init: bool
    is_skip_class_def: bool
    is_skip_private: bool
    files_info: tuple[FileCoverageStat, ...]
    needed: int
    found: int
    missing: int
    total_coverage: float
    grade: str


class Printer(ABC):
    """Base abstract superclass for printing coverage results."""

    def __init__(
        self,
        results: ResultCollection,
        verbosity: int,
        ignore_config: IgnoreConfig = IgnoreConfig(),
    ):
        self.verbosity = verbosity
        self.ignore_config = ignore_config
        self.overall_coverage_info = self._collect_info(results)

    def _collect_info(self, results: ResultCollection) -> OverallCoverageStat:
        """Collecting info data for later printing"""
        count = results.count_aggregate()

        return OverallCoverageStat(
            num_empty_files=count.num_empty_files,
            num_files=count.num_files,
            is_skip_magic=self.ignore_config.skip_magic,
            is_skip_file_docstring=self.ignore_config.skip_file_docstring,
            is_skip_init=self.ignore_config.skip_init,
            is_skip_class_def=self.ignore_config.skip_class_def,
            is_skip_private=self.ignore_config.skip_private,
            files_info=tuple(
                self._collect_file_coverage_info(file_path, file_info)
                for file_path, file_info in results.files()
            ),
            needed=count.needed,
            found=count.found,
            missing=count.missing,
            total_coverage=count.coverage(),
            grade=next(
                message for message, grade_threshold in _GRADES
                if grade_threshold <= count.coverage()
            ),
        )

    def _collect_file_coverage_info(self, file_path, file_info) -> FileCoverageStat:
        count = file_info.count_aggregate()

        return FileCoverageStat(
            path=file_path,
            is_empty=file_info.status == FileStatus.EMPTY,
            nodes_with_docstring=tuple(
                expected_docstring.node_identifier
                for expected_docstring in file_info._expected_docstrings
                if expected_docstring.has_docstring and not expected_docstring.ignore_reason
            ),
            nodes_without_docstring=tuple(
                expected_docstring.node_identifier
                for expected_docstring in file_info._expected_docstrings
                if not expected_docstring.has_docstring and not expected_docstring.ignore_reason
            ),
            ignored_nodes=tuple(
                IgnoredNode(
                    identifier=expected_docstring.node_identifier,
                    reason=expected_docstring.ignore_reason,
                )
                for expected_docstring in file_info._expected_docstrings
                if expected_docstring.ignore_reason is not None
            ),
            needed=count.needed,
            found=count.found,
            missing=count.missing,
            coverage=count.coverage(),
        )

    @abstractmethod
    def print(self) -> None:
        """Prints a provided set of results to stdout.

        Parameters
        ----------
        results: ResultCollection
            The information about docstr presence to be printed to stdout."""
        pass


class LegacyPrinter(Printer):
    """Print in simple format to output"""

    def _print_line(self, line: str = ""):
        """Prints `line`

        Parameters
        ----------
        line: String
            The text to print"""
        logger.info(line)

    def print(self):
        if self.verbosity >= 2:
            self._print_files_statistic()
        if self.verbosity >= 1:
            self._print_overall_statistics()

    def _print_overall_statistics(self):
        postfix = ""
        if self.overall_coverage_info.num_empty_files > 0:
            postfix = " (%s files are empty)" % self.overall_coverage_info.num_empty_files
        if self.overall_coverage_info.is_skip_magic:
            postfix += " (skipped all non-init magic methods)"
        if self.overall_coverage_info.is_skip_file_docstring:
            postfix += " (skipped file-level docstrings)"
        if self.overall_coverage_info.is_skip_init:
            postfix += " (skipped __init__ methods)"
        if self.overall_coverage_info.is_skip_class_def:
            postfix += " (skipped class definitions)"
        if self.overall_coverage_info.is_skip_private:
            postfix += " (skipped private methods)"

        if self.overall_coverage_info.num_files > 1:
            self._print_line("Overall statistics for %s files%s:" % (
                self.overall_coverage_info.num_files,
                postfix,
            ))
        else:
            self._print_line("Overall statistics%s:" % postfix)

        self._print_line(
            "Needed: {}  -  Found: {}  -  Missing: {}".format(
                self.overall_coverage_info.needed,
                self.overall_coverage_info.found,
                self.overall_coverage_info.missing,
            ),
        )

        self._print_line(
            "Total coverage: {:.1f}%  -  Grade: {}".format(
                self.overall_coverage_info.total_coverage,
                self.overall_coverage_info.grade,
            )
        )

    def _print_files_statistic(self):
        for file_info in self.overall_coverage_info.files_info:

            if self.verbosity < 4 and file_info.missing == 0:
                continue

            self._print_line('\nFile: "{0}"'.format(file_info.path))
            if self.verbosity >= 3:
                if file_info.is_empty and self.verbosity > 3:
                    self._print_line(" - File is empty")
                for node_identifier in file_info.nodes_with_docstring:
                    if self.verbosity > 3:
                        self._print_line(" - Found docstring for `{0}`".format(node_identifier))
                for ignored_node in file_info.ignored_nodes:
                    if self.verbosity > 3:
                        self._print_line(
                            " - Ignored `{0}`: reason: `{1}`".format(
                                ignored_node.identifier,
                                ignored_node.reason,
                            )
                        )
                for node_identifier in file_info.nodes_without_docstring:
                    if node_identifier == "module docstring":
                        self._print_line(" - No module docstring")
                    else:
                        self._print_line(" - No docstring for `{0}`".format(node_identifier))

            self._print_line(
                " Needed: %s; Found: %s; Missing: %s; Coverage: %.1f%%"
                % (
                    file_info.needed,
                    file_info.found,
                    file_info.missing,
                    file_info.coverage,
                )
            )
            self._print_line()
        self._print_line()
