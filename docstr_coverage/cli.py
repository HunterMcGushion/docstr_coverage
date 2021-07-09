"""This module is the CLI entry point for `docstr_coverage` in which CLI arguments are defined and
passed on to other modules"""
import os
import platform
import re
import sys
import warnings
from typing import List, Optional

import click

from docstr_coverage.badge import Badge
from docstr_coverage.config_file import set_config_defaults
from docstr_coverage.coverage import analyze
from docstr_coverage.ignore_config import IgnoreConfig
from docstr_coverage.printers import LegacyPrinter


def do_include_filepath(filepath: str, exclude_re: Optional["re.Pattern"]) -> bool:
    """Determine whether `filepath` should be included in docstring search.
    Note on regex matching:
    On windows we check against unix and windows regex matches (if one of the two matches)
    Hence we have a one-way compatibility (regex for unix paths work in win as well).
    Two way compatibility (matching win-path regexes on linux) is not possible as a single backslash
    is a valid character in a unix path.

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
        if exclude_re.match(filepath):
            return False
        if platform.system() == "Windows":
            return not exclude_re.match(filepath.replace("\\", "/"))
    return True


def collect_filepaths(
    *paths: str, follow_links: bool = False, exclude: Optional[str] = None
) -> List[str]:
    """Collect filepaths under given `paths` that are not `exclude`-d

    Parameters
    ----------
    *paths: String
        Path(s) to a directory/file from which filepaths will be collected
    follow_links: Boolean, default=False
        Whether to follow symbolic links when traversing directories in `paths`
    exclude: String (optional)
        If not None, used as a regex Pattern to exclude filepaths during collection. If a full
        filepath matches the `exclude` pattern, it is skipped

    Returns
    -------
    List
        List of string filepaths found under `paths` that are not excluded. If `paths` is a single
        ".py" file, result will be [`paths`]. Otherwise, the contents of `paths` that are not
        `exclude`-d will comprise the result"""
    exclude_re = re.compile(r"{}".format(exclude)) if exclude else None
    filepaths = []

    for path in paths:
        if path.endswith(".py"):
            filepaths.append(path)
        else:
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


def parse_ignore_patterns_from_dict(ignore_patterns_dict) -> tuple:
    """Parse dictionary containing (file_name_pattern, exclude_patterns) key value pairs
    to return an output consistent with ignore patterns parsed by `parse_ignore_names_file`

    Parameters
    ----------
    ignore_patterns_dict: Dict
        A dict where each key is a string and each value is a string or a nonempty list of strings.

    Returns
    -------
    Tuple
        Tuple of iterables of string with the same form as the output of `parse_ignore_names_file`

    Notes
    -----
    To align the workflow with `parse_ignore_names_file`, we check that the passed values
    are of type string, but we do not yet check if they are valid regular expressions"""

    def _assert_valid_key_value(k, v):
        if not isinstance(k, str):
            raise TypeError("ignore patterns in config contained non-string key {}".format(k))
        if len(k.strip()) == 0:
            raise ValueError("ignore pattern in config contained empty (file name) regex")
        if not all(isinstance(v, str) for v in v) and len(v) > 0:
            raise TypeError(
                "ignore patterns for key {} contained non-string values or was empty.".format(k)
            )
        if not all(len(v.strip()) > 0 for v in v):
            raise ValueError("ignore pattern for key {} contained empty regex".format(k))

    if not isinstance(ignore_patterns_dict, dict):
        raise TypeError(
            "ignore patterns in config must have type Dict[str, Union[str, List[str]]],"
            "but was {}".format(type(ignore_patterns_dict))
        )

    result_list = []
    for key, value in ignore_patterns_dict.items():
        res = [key]
        if not isinstance(value, list):
            value = [value]
        _assert_valid_key_value(key, value)
        res += value
        result_list.append(res)

    return tuple(result_list)


@click.command()
@click.option(
    "-v",
    "--verbose",
    type=click.Choice(["0", "1", "2", "3", "4"]),
    default="3",
    help="Verbosity level",
    show_default=True,
    callback=lambda _ctx, _param, value: int(value),
)
@click.option(
    "-e",
    "--exclude",
    type=str,
    default=None,
    help="Regex identifying filepaths to exclude",
    show_default=False,
    # TODO: Add support for multiple `--exclude` regex invocations
)
@click.option(
    "-m",
    "--skip-magic",
    is_flag=True,
    help="Ignore docstrings of magic methods (except `__init__`)",
)
@click.option("-f", "--skip-file-doc", is_flag=True, help="Ignore module docstrings")
@click.option("-i", "--skip-init", is_flag=True, help="Ignore docstrings of `__init__` methods")
@click.option("-c", "--skip-class-def", is_flag=True, help="Ignore docstrings of class definitions")
@click.option(
    "-sp", "--skip-property", is_flag=True, help="Ignore functions with @property decorator"
)
@click.option(
    "-is",
    "--include-setter",
    is_flag=True,
    help="Include functions with @setter decorator (default: ignored)",
)
@click.option(
    "-idel",
    "--include-deleter",
    is_flag=True,
    help="Include functions with @deleter decorator (default: ignored)",
)
@click.option(
    "-P",
    "--skip-private",
    is_flag=True,
    help="Ignore docstrings of functions starting with a single underscore",
)
@click.option("-l", "--follow-links", is_flag=True, help="Follow symlinks")
@click.option(
    "-d",
    "--docstr-ignore-file",
    "ignore_names_file",  # TODO: Remove after deprecating in favor of pyproject.toml `blacklist`
    type=click.Path(exists=False, resolve_path=True),
    default=".docstr_coverage",
    help="Filepath containing list of regex (file-pattern, name-pattern) pairs",
    show_default=True,
)
@click.option(
    "-F",
    "--fail-under",
    type=float,
    default=100.0,
    help="Fail when coverage % is less than a given amount",
    show_default=True,
    metavar="NUMBER",
)
@click.option(
    "-b",
    "--badge",
    type=click.Path(exists=False, resolve_path=True),
    default=None,
    help="Generate a docstring coverage percent badge as an SVG saved to a given filepath",
    show_default=False,
)
@click.option(
    "-p",
    "--percentage-only",
    is_flag=True,
    help="Output only the overall coverage percentage as a float, silencing all other logging",
)
@click.option(
    "-a",
    "--accept-empty",
    is_flag=True,
    help="Exit with code 0 if no Python files are found (default: exit code 1)",
)
@click.help_option("-h", "--help")
@click.argument(
    "paths",
    type=click.Path(exists=True, file_okay=True, dir_okay=True, readable=True, resolve_path=True),
    nargs=-1,
    is_eager=True,  # Eagerly execute before `config` so `set_config_defaults` has `paths`
)
@click.option(
    "-C",
    "--config",
    type=click.Path(exists=False, resolve_path=True),
    default=".docstr.yaml",
    help="Configuration file containing option defaults",
    is_eager=True,
    callback=set_config_defaults,
)
@click.option("--skipmagic", is_flag=True, help="Deprecated. Use --skip-magic")
@click.option("--skipfiledoc", is_flag=True, help="Deprecated. Use --skip-file-doc")
@click.option("--skipinit", is_flag=True, help="Deprecated. Use --skip-init")
@click.option("--skipclassdef", is_flag=True, help="Deprecated. Use --skip-class-def")
@click.option("--followlinks", is_flag=True, help="Deprecated. Use --follow-links")
@click.option("--failunder", type=float, help="Deprecated. Use --fail-under")
def execute(paths, **kwargs):
    """Measure docstring coverage for `PATHS`"""
    for deprecated_name, name in [
        ("skipmagic", "skip_magic"),
        ("skipfiledoc", "skip_file_doc"),
        ("skipinit", "skip_init"),
        ("skipclassdef", "skip_class_def"),
        ("followlinks", "follow_links"),
    ]:
        if kwargs.get(deprecated_name):
            new_flag = name.replace("_", "-")
            if kwargs.get(name):
                raise ValueError(
                    "Should not set deprecated --{} and new --{}".format(deprecated_name, new_flag)
                )
            click.secho(
                "Using deprecated --{}, should use --{}".format(deprecated_name, new_flag), fg="red"
            )
            kwargs[name] = kwargs.pop(deprecated_name)

    # handle fail under
    if kwargs.get("failunder") is not None:
        if kwargs.get("fail_under") != 100.0:
            raise ValueError("Should not set deprecated --failunder and --fail-under")
        click.secho("Using deprecated --failunder, should use --fail-under", fg="red")
        kwargs["fail_under"] = kwargs.pop("failunder")

    # TODO: Add option to generate pretty coverage reports - Like Python's test `coverage`
    # TODO: Add option to sort reports by filename, coverage score... (ascending/descending)
    if kwargs["percentage_only"] is True:
        # Override verbosity to ensure only the overall percentage is printed
        kwargs["verbose"] = 0

    all_paths = collect_filepaths(
        *paths, follow_links=kwargs["follow_links"], exclude=kwargs["exclude"]
    )

    if len(all_paths) < 1:
        if kwargs["accept_empty"] is True:
            warnings.warn("No Python files found in specified paths. Processing aborted")
            sys.exit(0)
        else:
            sys.exit(
                "No Python files found. "
                "Use `--accept-empty` to exit with code 0 if you expect this case, "
                "or specify the paths you'd like to check "
                "via command line arguments or the config file."
            )

    # Parse ignore names file
    has_ignore_patterns_in_config = "ignore_patterns" in kwargs
    if os.path.isfile(kwargs["ignore_names_file"]) and has_ignore_patterns_in_config:
        raise ValueError(
            (
                "The docstr-coverage configuration file {} contains ignore_patterns,"
                " and at the same time an ignore file {} was found."
                " Ignore patterns must be specified in only one location at a time."
            ).format(kwargs["config_file"], kwargs["ignore_names_file"])
        )
    elif os.path.isfile(kwargs["ignore_names_file"]):
        ignore_names = parse_ignore_names_file(kwargs["ignore_names_file"])
    elif has_ignore_patterns_in_config:
        ignore_names = parse_ignore_patterns_from_dict(kwargs["ignore_patterns"])
    else:
        ignore_names = []

    ignore_config = IgnoreConfig(
        skip_magic=kwargs["skip_magic"],
        skip_file_docstring=kwargs["skip_file_doc"],
        skip_init=kwargs["skip_init"],
        skip_class_def=kwargs["skip_class_def"],
        skip_private=kwargs["skip_private"],
        skip_property=kwargs["skip_property"],
        skip_setter=not kwargs["include_setter"],
        skip_deleter=not kwargs["include_deleter"],
        ignore_names=ignore_names,
    )

    # Calculate docstring coverage
    results = analyze(all_paths, ignore_config=ignore_config)

    LegacyPrinter(verbosity=kwargs["verbose"], ignore_config=ignore_config).print(results)

    file_results, total_results = results.to_legacy()

    # Save badge
    if kwargs["badge"]:
        badge = Badge(kwargs["badge"], total_results["coverage"])
        badge.save()

        if kwargs["verbose"]:
            print("Docstring coverage badge saved to {!r}".format(badge.path))

    if kwargs["percentage_only"] is True:
        print(total_results["coverage"])

    # Exit
    if total_results["coverage"] < kwargs["fail_under"]:
        raise SystemExit(1)

    raise SystemExit(0)


if __name__ == "__main__":
    execute()
