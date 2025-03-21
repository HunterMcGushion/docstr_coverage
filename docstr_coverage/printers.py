"""All logic used to print a recorded ResultCollection to stdout.
Currently, this module is in BETA and its interface may change in future versions."""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.result_collection import (
    AggregatedCount,
    File,
    FileStatus,
    ResultCollection,
)

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


@dataclass(frozen=True)
class IgnoredNode:
    """Data Structure for nodes that was ignored in checking."""

    identifier: str
    reason: str


@dataclass(frozen=True)
class FileCoverageStat:
    """Data Structure of coverage info about one file.

    For `verbosity` with value:
        * `2` - Fields `coverage`, `found`, `missing`, `needed` and `path`.
        * `3` - Fields with `verbosity` `2` and `nodes_without_docstring`.
        * `4` - Fields with `verbosity` `3` and `is_empty`, `nodes_with_docstring`,
          `ignored_nodes`
    """

    coverage: float
    found: int
    missing: int
    needed: int
    path: str
    ignored_nodes: Optional[Tuple[IgnoredNode, ...]]
    is_empty: Optional[Union[bool]]
    nodes_with_docstring: Optional[Tuple[str, ...]]
    nodes_without_docstring: Optional[Tuple[str, ...]]


@dataclass(frozen=True)
class OverallCoverageStat:
    """Data Structure of coverage statistic."""

    found: int
    grade: str
    is_skip_class_def: bool
    is_skip_file_docstring: bool
    is_skip_init: bool
    is_skip_magic: bool
    is_skip_private: bool
    is_skip_mangled: bool
    missing: int
    needed: int
    num_empty_files: int
    num_files: int
    total_coverage: float


class Printer(ABC):
    """Base abstract superclass for printing coverage results.

    It provides coverage results in data structures (`OverallCoverageStat`, `FileCoverageStat` and
    `IgnoredNode`) and abstract methods for implementing type of displaying and saving in file
    statistic data.

    In heir classes you can use `overall_coverage_stat` and `overall_files_coverage_stat`
    attributes. Depends of given `verbosity` some data can be `None`."""

    def __init__(
        self,
        results: ResultCollection,
        verbosity: int,
        ignore_config: IgnoreConfig = IgnoreConfig(),
    ):
        """
        Parameters
        ----------
        results: ResultCollection
            Coverage analyze results.
        verbosity: int
            Verbosity identifier.
        ignore_config: IgnoreConfig
            Config with ignoring setups.
        """
        self.verbosity: int = verbosity
        self.ignore_config: IgnoreConfig = ignore_config
        self.results: ResultCollection = results
        self.__overall_coverage_stat: Optional[Union[OverallCoverageStat, float]] = None
        self.__overall_files_coverage_stat: Optional[List[FileCoverageStat]] = None

    @property
    def overall_coverage_stat(self) -> Union[OverallCoverageStat, float]:
        """Getting full coverage statistic.

        For `verbosity` with value:
            * `0` - Only `total_coverage` value returning.
            * `1` - All fields, except `files_info`.
            * `2` - All fields."""
        if self.__overall_coverage_stat is None:
            count: AggregatedCount = self.results.count_aggregate()

            if self.verbosity >= 1:

                self.__overall_coverage_stat = OverallCoverageStat(
                    found=count.found,
                    grade=next(
                        message
                        for message, grade_threshold in _GRADES
                        if grade_threshold <= count.coverage()
                    ),
                    is_skip_class_def=self.ignore_config.skip_class_def,
                    is_skip_file_docstring=self.ignore_config.skip_file_docstring,
                    is_skip_init=self.ignore_config.skip_init,
                    is_skip_magic=self.ignore_config.skip_magic,
                    is_skip_private=self.ignore_config.skip_private,
                    is_skip_mangled=self.ignore_config.skip_mangled,
                    missing=count.missing,
                    needed=count.needed,
                    num_empty_files=count.num_empty_files,
                    num_files=count.num_files,
                    total_coverage=count.coverage(),
                )

            else:
                self.__overall_coverage_stat = count.coverage()

        return self.__overall_coverage_stat

    @property
    def overall_files_coverage_stat(self) -> Optional[List[FileCoverageStat]]:
        """Getting coverage statistics for files.

        For `verbosity` with value:
            * `2` - Fields `coverage`, `found`, `missing`, `needed` and `path`.
            * `3` - Fields with `verbosity` `2` and `nodes_without_docstring`.
            * `4` - Fields with `verbosity` `3` and `is_empty`, `nodes_with_docstring`,
              `ignored_nodes`

        Returns
        -------
        List[FileCoverageStat]
            Coverage info about all checked files."""
        if self.__overall_files_coverage_stat is None and self.verbosity >= 2:
            overall_files_coverage_stat: List[FileCoverageStat] = []
            for file_path, file_info in self.results.files():

                file_path: str
                file_info: File
                nodes_without_docstring: Optional[Tuple[str, ...]]
                is_empty: Optional[bool]
                nodes_with_docstring: Optional[Tuple[str, ...]]
                ignored_nodes: Optional[Tuple[IgnoredNode, ...]]

                if self.verbosity >= 3:
                    nodes_without_docstring = tuple(
                        expected_docstring.node_identifier
                        for expected_docstring in file_info._expected_docstrings
                        if not expected_docstring.has_docstring
                        and not expected_docstring.ignore_reason
                    )
                else:
                    nodes_without_docstring = None

                if self.verbosity >= 4:
                    is_empty = file_info.status == FileStatus.EMPTY
                    nodes_with_docstring = tuple(
                        expected_docstring.node_identifier
                        for expected_docstring in file_info._expected_docstrings
                        if expected_docstring.has_docstring and not expected_docstring.ignore_reason
                    )
                    ignored_nodes = tuple(
                        IgnoredNode(
                            identifier=expected_docstring.node_identifier,
                            reason=expected_docstring.ignore_reason,
                        )
                        for expected_docstring in file_info._expected_docstrings
                        if expected_docstring.ignore_reason is not None
                    )
                else:
                    is_empty = None
                    nodes_with_docstring = None
                    ignored_nodes = None

                count = file_info.count_aggregate()
                overall_files_coverage_stat.append(
                    FileCoverageStat(
                        coverage=count.coverage(),
                        found=count.found,
                        missing=count.missing,
                        needed=count.needed,
                        path=file_path,
                        ignored_nodes=ignored_nodes,
                        is_empty=is_empty,
                        nodes_with_docstring=nodes_with_docstring,
                        nodes_without_docstring=nodes_without_docstring,
                    )
                )
            self.__overall_files_coverage_stat = overall_files_coverage_stat

        return self.__overall_files_coverage_stat

    @abstractmethod
    def print_to_stdout(self) -> None:
        """Providing how to print coverage results."""
        pass

    @abstractmethod
    def save_to_file(self, path: Optional[str] = None) -> None:
        """Providing how to save coverage results in file.

        Parameters
        ----------
        path: Optional[str]
            Path to file with coverage results.
        """
        pass


class LegacyPrinter(Printer):
    """Printer for legacy format."""

    def print_to_stdout(self) -> None:
        for line in self._generate_string().split("\n"):
            logger.info(line)

    def save_to_file(self, path: Optional[str] = None) -> None:
        if path is None:
            path = "./coverage-results.txt"
        with open(path, "w") as wf:
            wf.write(self._generate_string())

    def _generate_string(self) -> str:
        final_string: str = ""

        if self.overall_files_coverage_stat is not None:
            final_string += self._generate_file_stat_string()
            final_string += "\n"
        final_string += self._generate_overall_stat_string()

        return final_string

    def _generate_file_stat_string(self):
        final_string: str = ""
        for file_coverage_stat in self.overall_files_coverage_stat:

            file_string: str = 'File: "{0}"\n'.format(file_coverage_stat.path)

            if file_coverage_stat.is_empty is not None and file_coverage_stat.is_empty is True:
                file_string += " - File is empty\n"

            if file_coverage_stat.nodes_with_docstring is not None:
                for node_identifier in file_coverage_stat.nodes_with_docstring:
                    file_string += " - Found docstring for `{0}`\n".format(
                        node_identifier,
                    )

            if file_coverage_stat.ignored_nodes is not None:
                for ignored_node in file_coverage_stat.ignored_nodes:
                    file_string += " - Ignored `{0}`: reason: `{1}`\n".format(
                        ignored_node.identifier,
                        ignored_node.reason,
                    )

            if file_coverage_stat.nodes_without_docstring is not None:
                for node_identifier in file_coverage_stat.nodes_without_docstring:
                    if node_identifier == "module docstring":
                        file_string += " - No module docstring\n"
                    else:
                        file_string += " - No docstring for `{0}`\n".format(node_identifier)

            file_string += " Needed: %s; Found: %s; Missing: %s; Coverage: %.1f%%" % (
                file_coverage_stat.needed,
                file_coverage_stat.found,
                file_coverage_stat.missing,
                file_coverage_stat.coverage,
            )

            final_string += "\n" + file_string + "\n"

        return final_string + "\n"

    def _generate_overall_stat_string(self) -> str:
        if isinstance(self.overall_coverage_stat, float):
            return str(self.overall_coverage_stat)

        prefix: str = ""

        if self.overall_coverage_stat.num_empty_files > 0:
            prefix += " (%s files are empty)" % self.overall_coverage_stat.num_empty_files

        if self.overall_coverage_stat.is_skip_magic:
            prefix += " (skipped all non-init magic methods)"

        if self.overall_coverage_stat.is_skip_file_docstring:
            prefix += " (skipped file-level docstrings)"

        if self.overall_coverage_stat.is_skip_init:
            prefix += " (skipped __init__ methods)"

        if self.overall_coverage_stat.is_skip_class_def:
            prefix += " (skipped class definitions)"

        if self.overall_coverage_stat.is_skip_private:
            prefix += " (skipped private methods)"

        if self.overall_coverage_stat.is_skip_mangled:
            prefix += " (skipped mangled method names)"

        final_string: str = ""

        if self.overall_coverage_stat.num_files > 1:
            final_string += "Overall statistics for %s files%s:\n" % (
                self.overall_coverage_stat.num_files,
                prefix,
            )
        else:
            final_string += "Overall statistics%s:\n" % prefix

        final_string += "Needed: {}  -  Found: {}  -  Missing: {}\n".format(
            self.overall_coverage_stat.needed,
            self.overall_coverage_stat.found,
            self.overall_coverage_stat.missing,
        )

        final_string += "Total coverage: {:.1f}%  -  Grade: {}".format(
            self.overall_coverage_stat.total_coverage,
            self.overall_coverage_stat.grade,
        )

        return final_string


class MarkdownPrinter(LegacyPrinter):
    """Printer for Markdown format."""

    def save_to_file(self, path: Optional[str] = None) -> None:
        if path is None:
            path = "./coverage-results.md"
        with open(path, "w") as wf:
            wf.write(self._generate_string())

    def _generate_file_stat_string(self) -> str:
        final_string: str = ""
        for file_coverage_stat in self.overall_files_coverage_stat:

            file_string: str = "**File**: `{0}`\n".format(file_coverage_stat.path)

            if file_coverage_stat.is_empty is not None and file_coverage_stat.is_empty is True:
                file_string += "- File is empty\n"

            if file_coverage_stat.nodes_with_docstring is not None:
                for node_identifier in file_coverage_stat.nodes_with_docstring:
                    file_string += "- Found docstring for `{0}`\n".format(
                        node_identifier,
                    )

            if file_coverage_stat.ignored_nodes is not None:
                for ignored_node in file_coverage_stat.ignored_nodes:
                    file_string += "- Ignored `{0}`: reason: `{1}`\n".format(
                        ignored_node.identifier,
                        ignored_node.reason,
                    )

            if file_coverage_stat.nodes_without_docstring is not None:
                for node_identifier in file_coverage_stat.nodes_without_docstring:
                    if node_identifier == "module docstring":
                        file_string += "- No module docstring\n"
                    else:
                        file_string += "- No docstring for `{0}`\n".format(node_identifier)

            file_string += "\n"

            file_string += self._generate_markdown_table(
                ("Needed", "Found", "Missing", "Coverage"),
                (
                    (
                        file_coverage_stat.needed,
                        file_coverage_stat.found,
                        file_coverage_stat.missing,
                        "{:.1f}%".format(file_coverage_stat.coverage),
                    ),
                ),
            )

            if final_string == "":
                final_string += file_string + "\n"
            else:
                final_string += "\n" + file_string + "\n"

        return final_string + "\n"

    def _generate_overall_stat_string(self) -> str:
        if isinstance(self.overall_coverage_stat, float):
            return str(self.overall_coverage_stat)

        final_string: str = "## Overall statistics\n"

        if self.overall_coverage_stat.num_files > 1:
            final_string += "Files number: **{}**\n".format(self.overall_coverage_stat.num_files)

        final_string += "\n"

        final_string += "Total coverage: **{:.1f}%**\n".format(
            self.overall_coverage_stat.total_coverage,
        )

        final_string += "\n"

        final_string += "Grade: **{}**\n".format(self.overall_coverage_stat.grade)

        if self.overall_coverage_stat.num_empty_files > 0:
            final_string += "- %s files are empty\n" % self.overall_coverage_stat.num_empty_files

        if self.overall_coverage_stat.is_skip_magic:
            final_string += "- skipped all non-init magic methods\n"

        if self.overall_coverage_stat.is_skip_file_docstring:
            final_string += "- skipped file-level docstrings\n"

        if self.overall_coverage_stat.is_skip_init:
            final_string += "- skipped __init__ methods\n"

        if self.overall_coverage_stat.is_skip_class_def:
            final_string += "- skipped class definitions\n"

        if self.overall_coverage_stat.is_skip_private:
            final_string += "- skipped private methods\n"

        if self.overall_coverage_stat.is_skip_mangled:
            final_string += "- skipped mangled method names\n"

        final_string += "\n"

        final_string += self._generate_markdown_table(
            ("Needed", "Found", "Missing"),
            (
                (
                    self.overall_coverage_stat.needed,
                    self.overall_coverage_stat.found,
                    self.overall_coverage_stat.missing,
                ),
            ),
        )

        return final_string

    def _generate_markdown_table(
        self,
        cols: Tuple[str, ...],
        rows: Tuple[Tuple[Union[str, int, float]], ...],
    ) -> str:
        """Generate markdown table.

        Using:
        >>> self._generate_markdown_table(
        ...     cols=("Needed", "Found", "Missing"),
        ...     vals=(
        ...         (10, 20, "65.5%"),
        ...         (30, 40, "99.9%")
        ...     )
        ... )
        | Needed | Found | Missing |
        |---|---|---|
        | 10 | 20 | 65.5% |
        | 30 | 40 | 99.9% |

        Parameters
        ----------
        cols: Tuple[str, ...]
            Table columns
        rows: Tuple[Tuple[Union[str, int, float]], ...]
            Column values

        Returns
        -------
        str
            Generated table.
        """
        if not all(len(v) == len(cols) for v in rows):
            raise ValueError("Col num not equal to cols value")
        final_string: str = ""

        for col in cols:
            final_string += "| {} ".format(col)
        final_string += "|\n"

        for _ in range(len(cols)):
            final_string += "|---"
        final_string += "|\n"

        for row in rows:
            for value in row:
                final_string += "| {} ".format(value)
            final_string += "|"

        return final_string
