"""This module is the CLI entry point for `docstr_coverage` in which CLI arguments are defined and
passed on to other modules"""
from optparse import OptionParser

# TODO: Replace deprecated optparse: https://pythonprogramminglanguage.com/command-line-arguments/
import os
from pathlib import Path
import re
import sys
from typing import List, Optional

from docstr_coverage.badge import Badge
from docstr_coverage.coverage import get_docstring_coverage


def do_include_filepath(filepath: str, exclude_re: Optional["re.Pattern"]) -> bool:
    """Determine whether `filepath` should be included in docstring search

    Parameters
    ----------
    filepath: String
        Filepath to match with `exclude_re`. If extension is not ".py", it will be excluded
    exclude_re: re.Pattern, or None
        Pattern for files to be excluded. If None, `exclude_re` is ignored

    Returns
    -------
    Boolean
        True if `filepath` should be searched, else False"""
    if not filepath.endswith(".py"):
        return False
    if exclude_re is not None:
        return not exclude_re.match(filepath)
    return True


def collect_filepaths(
    path: str, follow_links: bool = False, exclude: Optional[str] = None
) -> List[str]:
    """Collect filepaths under a given `path` that are not `exclude`-d

    Parameters
    ----------
    path: String
        Path to a directory/file from which filepaths will be collected
    follow_links: Boolean, default=False
        Whether to follow symbolic links when traversing directories in `path`
    exclude: String (optional)
        If not None, used as a regex Pattern to exclude filepaths during collection. If a full
        filepath matches the `exclude` pattern, it is skipped

    Returns
    -------
    List
        List of string filepaths found under `path` that are not excluded. If `path` is a ".py"
        file, result will be [`path`]. Otherwise, the contents of `path` that are not `exclude`-d
        will comprise the result"""
    exclude_re = re.compile(r"{}".format(exclude)) if exclude else None
    filepaths = []

    if path.endswith(".py"):
        return [path]

    for (dirpath, dirnames, filenames) in os.walk(path, followlinks=follow_links):
        candidates = [os.path.join(dirpath, _) for _ in filenames]
        filepaths.extend([_ for _ in candidates if do_include_filepath(_, exclude_re)])

    return sorted(filepaths)


def parse_ignore_names_file(ignore_names_file: str) -> tuple:
    """Parse a file containing patterns of names to ignore

    Parameters
    ----------
    ignore_names_file: String
        Path to a file containing name patterns

    Returns
    -------
    Tuple
        Tuple containing one list for each valid line in `ignore_names_file`. Each list contains
        the space-delimited contents of that line in the file, in which the first value is a file
        pattern, and all other values are name patterns"""
    if not os.path.isfile(ignore_names_file):
        return ()

    with open(ignore_names_file, "r") as f:
        ignore_names = tuple([line.split() for line in f.readlines() if " " in line])

    return ignore_names


def _execute():
    """Main command-line execution routine"""

    #################### Declare Options ####################
    parser = OptionParser()
    # TODO: Add option to generate pretty coverage reports - Like Python's `coverage`
    #       module does for test coverage
    # TODO: Add option to sort report summaries by filename,
    #       coverage score... (ascending/descending)
    parser.add_option(
        "-e",
        "--exclude",
        dest="exclude",
        default=None,
        type="string",
        help="Regex identifying filepaths to exclude",
    )
    # TODO: Add support for multiple `--exclude` regexes to lessen need
    #       for long regexes describing separate exclusion items
    parser.add_option(
        "-v",
        "--verbose",
        dest="verbose",
        default="3",
        metavar="LEVEL",
        help="Verbosity level <0-3>, default=3",
        type="choice",
        choices=["0", "1", "2", "3"],
    )
    parser.add_option(
        "-m",
        "--skipmagic",
        action="store_true",
        dest="skip_magic",
        default=False,
        help='Ignore docstrings of magic methods (except "__init__")',
    )
    parser.add_option(
        "-f",
        "--skipfiledoc",
        action="store_true",
        dest="skip_file_docstring",
        default=False,
        help="Ignore module docstrings",
    )
    parser.add_option(
        "-i",
        "--skipinit",
        action="store_true",
        dest="skip_init",
        default=False,
        help='Ignore docstrings of "__init__" methods',
    )
    parser.add_option(
        "-c",
        "--skipclassdef",
        action="store_true",
        dest="skip_class_def",
        default=False,
        help="Ignore docstrings of class definitions",
    )
    parser.add_option(
        "-l",
        "--followlinks",
        action="store_true",
        dest="follow_links",
        default=False,
        help="Follow symlinks",
    )
    parser.add_option(
        "-d",
        "--docstr-ignore-file",
        dest="ignore_names_file",
        default=".docstr_coverage",
        type="string",
        help="Filepath containing list of regex (file-pattern, name-pattern) pairs",
    )
    parser.add_option(
        "-F",
        "--failunder",
        dest="fail_under",
        type="float",
        default=100.0,
        metavar="FLOAT",
        help="Fail when coverage % is less than a given amount (default: 100.0)",
    )
    parser.add_option(
        "-b",
        "--badge",
        dest="badge_path",
        type="string",
        default=None,
        help="Generate a docstring coverage percent badge as an SVG saved to a given filepath",
    )
    # TODO: Separate above arg/option parsing into separate function;
    #       Document return values to describe allowed options.
    options, args = parser.parse_args()

    if len(args) != 1:
        print("Expected a single path argument. Received invalid argument(s): {}".format(args[1:]))
        sys.exit()

    path = args[0]
    filenames = collect_filepaths(path, follow_links=options.follow_links, exclude=options.exclude)

    if len(filenames) < 1:
        sys.exit("No Python files found")

    # Resolve path to ignore names file and parse contents
    if options.ignore_names_file == ".docstr_coverage":
        if path.endswith(".py"):
            path = "."
        options.ignore_names_file = Path(path, options.ignore_names_file)

    ignore_names = parse_ignore_names_file(options.ignore_names_file)

    # Calculate docstring coverage
    file_results, total_results = get_docstring_coverage(
        filenames,
        skip_magic=options.skip_magic,
        skip_file_docstring=options.skip_file_docstring,
        skip_init=options.skip_init,
        skip_class_def=options.skip_class_def,
        verbose=options.verbose,
        ignore_names=ignore_names,
    )

    # Save badge
    if options.badge_path:
        badge = Badge(options.badge_path, total_results["coverage"])
        badge.save()
        print("Docstring coverage badge saved to {!r}".format(badge.path))

    # Exit
    if total_results["coverage"] < options.fail_under:
        raise SystemExit(1)

    raise SystemExit(0)


if __name__ == "__main__":
    _execute()
