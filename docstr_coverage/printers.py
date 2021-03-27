import logging

from docstr_coverage.result_collection import ResultCollection, FileStatus

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


def print_line(line: str = ""):
    """Prints `line`

    Parameters
    ----------
    line: String
        The text to print

    """
    logger.info(line)


class LegacyPrinter:
    def __init__(
        self,
        verbosity: int,
        scip_magic,
        skip_file_docstring,
        skip_init,
        skip_class_def,
        skip_private,
    ):
        self.verbosity = verbosity
        self.skip_magic = scip_magic
        self.skip_file_docstring = skip_file_docstring
        self.skip_init = skip_init
        self.skip_class_def = skip_class_def
        self.skip_private = skip_private

    def print(self, results: ResultCollection):
        if self.verbosity >= 2:
            self._print_file_statistics(results)
        if self.verbosity >= 1:
            self._print_overall_statistics(results)

    def _print_file_statistics(self, results: ResultCollection):
        for file_path, file in results.files():
            # File Header
            print_line('\nFile: "{}"'.format(file_path))

            # List of missing docstrings
            if self.verbosity >= 3:
                if file.get_status() == FileStatus.EMPTY:
                    print_line(" - File is empty")
                for expected_docstr in file._expected_docstrings:
                    if not expected_docstr.has_docstring and not expected_docstr.ignore_reason:
                        if expected_docstr.node_identifier == "module docstring":
                            print_line(" - No module docstring")
                        else:
                            print_line(
                                " - No docstring for `{0}`".format(expected_docstr.node_identifier)
                            )

            # Statistics
            count = file.count()
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

    def _print_overall_statistics(self, results: ResultCollection):
        if self.verbosity < 1:
            return None

        count = results.count()

        postfix = ""
        if count.num_empty_files > 0:
            postfix = " (%s files are empty)" % count.num_empty_files
        if self.skip_magic:
            postfix += " (skipped all non-init magic methods)"
        if self.skip_file_docstring:
            postfix += " (skipped file-level docstrings)"
        if self.skip_init:
            postfix += " (skipped __init__ methods)"
        if self.skip_class_def:
            postfix += " (skipped class definitions)"
        if self.skip_private:
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

        #################### Calculate Total Grade ####################
        grade = next(
            message for message, grade_threshold in _GRADES if grade_threshold <= count.coverage()
        )

        print_line("Total coverage: {:.1f}%  -  Grade: {}".format(count.coverage(), grade))
