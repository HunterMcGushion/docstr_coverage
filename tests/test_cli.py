"""Tests for :mod:`docstr_coverage.cli`"""
import os
import re
import sys
from typing import List, Optional

import pytest
from click.testing import CliRunner

from docstr_coverage.cli import (
    collect_filepaths,
    do_include_filepath,
    execute,
    parse_ignore_names_file,
    parse_ignore_patterns_from_dict,
)


class Samples:
    def __init__(self, dirpath: str):
        """Convenience/helper class to organize paths to sample files

        Parameters
        ----------
        dirpath: String
            Path to a sample file subdirectory containing the required sample scripts"""
        self.dirpath = dirpath
        self.documented = os.path.join(dirpath, "documented_file.py")
        self.empty = os.path.join(dirpath, "empty_file.py")
        self.partial = os.path.join(dirpath, "partly_documented_file.py")
        self.undocumented = os.path.join(dirpath, "some_code_no_docs.py")

    @property
    def all(self) -> List[str]:
        """Get all of the sample script paths inside the subdirectory"""
        return [self.documented, self.empty, self.partial, self.undocumented]


CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLES_DIR = os.path.abspath(os.path.join(CWD, "sample_files"))
SAMPLES_A = Samples(os.path.join(SAMPLES_DIR, "subdir_a"))
SAMPLES_B = Samples(os.path.join(SAMPLES_DIR, "subdir_b"))


@pytest.fixture
def runner() -> CliRunner:
    """Click CliRunner fixture"""
    runner = CliRunner()
    return runner


@pytest.fixture(autouse=False, scope="function")
def cd_tests_dir_fixture():
    """Fixture to change current working directory to "docstr_coverage/tests" for the test's
    duration before returning to the original current working directory"""
    original_cwd = os.getcwd()
    os.chdir(CWD)
    yield
    os.chdir(original_cwd)


@pytest.fixture
def exclude_re(request) -> "re.Pattern":
    """Indirectly parametrized fixture that expects a string or None as input"""
    pattern = getattr(request, "param", None)
    return re.compile(r"{}".format(pattern)) if pattern else None


@pytest.mark.parametrize(
    ["filepath", "exclude_re", "expected"],
    [
        ("foo.js", None, False),
        ("foo.txt", None, False),
        ("foobar", None, False),
        ("foo_py.js", None, False),
        ("foo.py", None, True),
        ("foo/bar.py", None, True),
        ("foo.py", "bar", True),
        ("foo.py", "fo", False),
        ("foo.py", "foo.+\\.py", True),  # `exclude_re` requires something between "foo" and ".py"
        ("foo.py", "foo.+", False),  # ".+" applied to extension, so `filepath` is excluded
        ("foo_bar.py", "foo.+", False),
        ("foo_bar.py", "foo.+\\.py", False),
        ("foo/bar.py", "foo", False),
        ("foo/bar.py", "bar", True),
        ("foo/bar.py", ".*bar", False),
        ("foo/bar.py", "bar/", True),
        ("foo/bar/baz.py", "bar/.*", True),  # `exclude_re` starts with "bar"
        ("foo/bar/baz.py", ".*/bar/.*", False),
    ],
    indirect=["exclude_re"],
)
def test_do_include_filepath(filepath: str, exclude_re: Optional[str], expected: bool):
    """Test that :func:`docstr_coverage.cli.do_include_filepath` includes correct filepaths

    Parameters
    ----------
    filepath: String
        Filepath to match with `exclude_re`
    exclude_re: String, or None
        Pattern to check against `filepath`. Indirectly parametrized to be `re.Pattern` or None
    expected: Boolean
        Expected response to whether `filepath` should be included"""
    actual = do_include_filepath(filepath, exclude_re)
    assert actual is expected


@pytest.mark.parametrize(
    ["paths", "exclude", "expected"],
    [
        ([SAMPLES_DIR], "", SAMPLES_A.all + SAMPLES_B.all),
        ([SAMPLES_A.documented], "", [SAMPLES_A.documented]),
        ([SAMPLES_A.dirpath], "", SAMPLES_A.all),
        ([SAMPLES_A.dirpath], ".*/sample_files/.*", []),
        ([SAMPLES_A.dirpath], ".*documented_file.*", [SAMPLES_A.empty, SAMPLES_A.undocumented]),
        ([SAMPLES_A.empty, SAMPLES_A.documented], "", [SAMPLES_A.documented, SAMPLES_A.empty]),
        ([SAMPLES_A.dirpath, SAMPLES_B.dirpath], "", SAMPLES_A.all + SAMPLES_B.all),
        ([SAMPLES_A.dirpath, SAMPLES_B.dirpath], ".*subdir_a.*", SAMPLES_B.all),
        (
            [SAMPLES_A.dirpath, SAMPLES_B.documented, SAMPLES_B.empty],
            ".*subdir_a.*",
            [SAMPLES_B.documented, SAMPLES_B.empty],
        ),
        (
            [SAMPLES_A.dirpath, SAMPLES_B.dirpath],
            ".*_file\\.py",
            [SAMPLES_A.undocumented, SAMPLES_B.undocumented],
        ),
    ],
)
def test_collect_filepaths(paths: List[str], exclude: str, expected: List[str]):
    """Test that :func:`docstr_coverage.cli.collect_filepaths` includes correct filepaths

    Parameters
    ----------
    paths: List
        Path(s) to directory/file
    exclude: String
        Pattern for filepaths to exclude
    expected: List
        Expected list of filepaths to include in search"""
    actual = collect_filepaths(*paths, follow_links=False, exclude=exclude)
    assert actual == expected


# we could manually implement order-ignoring ==,
#   but I do not think its worth it, since py 3.6+ supports
#   it and thus runs the test
@pytest.mark.skipif(
    sys.version_info < (3, 6),
    reason="order-ignoring dict == comparison requires python3.6 or later ",
)
def test_ignore_patterns():
    """Test that parsing an ignore_pattern_dict (typically coming from yaml) leads
    to the expected list-of-string tuples"""
    dict_patterns = {
        "SomeFile": ["method_to_ignore1", "method_to_ignore2", "method_to_ignore3"],
        "FileWhereWeWantToIgnoreAllSpecialMethods": "__.+__",
        ".*": "method_to_ignore_in_all_files",
        "a_very_important_view_file": ["^get$", "^set$", "^post$"],
        "detect_.*": ["get_val.*"],
    }
    expected = (
        ["SomeFile", "method_to_ignore1", "method_to_ignore2", "method_to_ignore3"],
        ["FileWhereWeWantToIgnoreAllSpecialMethods", "__.+__"],
        [".*", "method_to_ignore_in_all_files"],
        ["a_very_important_view_file", "^get$", "^set$", "^post$"],
        ["detect_.*", "get_val.*"],
    )
    actual = parse_ignore_patterns_from_dict(dict_patterns)
    assert actual == expected


@pytest.mark.parametrize(
    ["input_dict", "error"],
    [
        ("not_a_dict", TypeError),  # Wrong type: not a dict
        ({0: ["get_val.*"]}, TypeError),  # Wrong type: non-string key
        ({"SomeFile": 0}, TypeError),  # Wrong type: non string non List[str]
        ({"SomeFile": [0]}, TypeError),  # Wrong type: non string non List[str]
        ({"SomeFile": {"asd", "adw"}}, TypeError),  # Wrong type: non string non List[str]
        ({" ": ["get_val.*"]}, ValueError),  # Empty string not permitted
        ({"SomeFile": ""}, ValueError),  # Empty string not permitted
        ({"SomeFile": " "}, ValueError),  # Empty string not permitted
    ],
)
def test_ignore_patterns_from_dict_errors(input_dict, error):
    """Test that invalid yaml ignore_pattern dicts raises an error

    Parameters
    ----------
    input_dict
        The faulty input
    error: Union[TypeError, ValueError]
        The expected error"""
    with pytest.raises(error):
        parse_ignore_patterns_from_dict(input_dict)


@pytest.mark.parametrize(
    ["path", "expected"],
    [
        ("", ()),
        ("this_file_does_not_exist.txt", ()),
        (
            os.path.join(SAMPLES_A.dirpath, "docstr_ignore.txt"),
            (
                ["SomeFile", "method_to_ignore1", "method_to_ignore2", "method_to_ignore3"],
                ["FileWhereWeWantToIgnoreAllSpecialMethods", "__.+__"],
                [".*", "method_to_ignore_in_all_files"],
                ["a_very_important_view_file", "^get$", "^set$", "^post$"],
                ["detect_.*", "get_val.*"],
            ),
        ),
    ],
)
def test_parse_ignore_names_file(path: str, expected: tuple):
    """Test that :func:`docstr_coverage.cli.parse_ignore_names_file` correctly parses patterns

    Parameters
    ----------
    path: String
        Path to a file containing patterns to ignore
    expected: Tuple
        Expected parsed patterns from `path`"""
    actual = parse_ignore_names_file(path)
    assert actual == expected


@pytest.mark.parametrize(
    ["paths", "expected_output"],
    [
        [[SAMPLES_A.dirpath], "62.5"],
        [[SAMPLES_A.partial], "20.0"],
        [[SAMPLES_A.documented], "100.0"],
        [[SAMPLES_A.undocumented], "0.0"],
        [[SAMPLES_A.undocumented, SAMPLES_A.documented], "81.81818181818181"],
    ],
)
@pytest.mark.parametrize("verbose_flag", [["-v", "0"], ["-v", "1"], ["-v", "2"], ["-v", "3"]])
def test_percentage_only(
    paths: List[str], expected_output: str, verbose_flag: List[str], runner: CliRunner
):
    """Test that using the `--percentage-only` CLI option works correctly

    Parameters
    ----------
    paths: List[str]
        Path arguments provided to CLI
    expected_output: String
        Expected stdout output of invoking the CLI command
    verbose_flag: List[str]
        Verbosity option with which to execute the command. `--percentage-only` should function the
        same regardless of verbosity, so this should basically be ignored
    runner: CliRunner
        Click utility to invoke command line scripts"""
    actual_output = runner.invoke(execute, ["--percentage-only"] + verbose_flag + paths)
    assert actual_output.stdout == "{}\n".format(expected_output)  # `print`'s default `end`="\n"


##################################################
# Click Tests
##################################################
@pytest.mark.parametrize(
    "paths",
    [
        pytest.param([SAMPLES_DIR], id="samples_dir_x1"),
        pytest.param([SAMPLES_A.documented], id="files_x1"),
        pytest.param([SAMPLES_A.empty, SAMPLES_A.partial], id="files_x2"),
        pytest.param([SAMPLES_A.dirpath, SAMPLES_B.dirpath], id="dirs_x2"),
        pytest.param([SAMPLES_A.empty, SAMPLES_A.partial, SAMPLES_B.dirpath], id="files_x2+dir_x1"),
        pytest.param([os.path.join("sample_files", "subdir_a")], id="rel_dir_x1"),
    ],
)
@pytest.mark.parametrize(
    ["follow_links_flag", "follow_links_value"],
    [
        pytest.param([], False, id="no_follow_links"),
        pytest.param(["-l"], True, id="short_follow_links"),
        pytest.param(["--followlinks"], True, id="long_follow_links"),
    ],
)
@pytest.mark.parametrize(
    ["exclude_flag", "exclude_value"],
    [
        pytest.param([], None, id="no_exclude"),
        pytest.param(["-e", ".*"], ".*", id="short_exclude_x1"),
        pytest.param(["--exclude", "foo"], "foo", id="long_exclude_x1"),
        pytest.param(["--exclude", "foo"], "foo", id="long_exclude_x1_2"),
        # TODO: Add cases with multiple short and long patterns, and combinations of short/long
    ],
)
@pytest.mark.usefixtures("cd_tests_dir_fixture")
def test_cli_collect_filepaths(
    paths: List[str],
    follow_links_flag: List[str],
    follow_links_value: bool,
    exclude_flag: List[str],
    exclude_value: Optional[str],
    runner: CliRunner,
    mocker,
):
    """Test that CLI inputs are correctly interpreted and passed along to
    :func:`docstr_coverage.cli.collect_filepaths`

    Parameters
    ----------
    paths: List[str]
        Path arguments provided to CLI. These should be made absolute before they are passed to
        :func:`docstr_coverage.cli.collect_filepaths`
    follow_links_flag: List[str]
        CLI option input for whether symbolic links should be followed
    follow_links_value: Boolean
        Processed value of `follow_links_flag` expected by function call
    exclude_flag: List[str]
        CLI option input for paths to exclude from search
    exclude_value: String, or None
        Processed value of `exclude_flag` expected by function call
    runner: CliRunner
        Click utility to invoke command line scripts
    mocker: pytest_mock.MockFixture
        Mock to check arguments passed to :func:`docstr_coverage.cli.collect_filepaths`"""
    mock_collect_filepaths = mocker.patch("docstr_coverage.cli.collect_filepaths")

    runner.invoke(execute, follow_links_flag + exclude_flag + paths)

    mock_collect_filepaths.assert_called_once_with(
        *[os.path.abspath(_) for _ in paths], follow_links=follow_links_value, exclude=exclude_value
    )


@pytest.mark.parametrize(
    "paths",
    [
        pytest.param([SAMPLES_DIR], id="samples_dir_x1"),
        pytest.param([SAMPLES_A.documented], id="files_x1"),
        pytest.param([SAMPLES_A.empty, SAMPLES_A.partial], id="files_x2"),
        pytest.param([SAMPLES_A.dirpath, SAMPLES_B.dirpath], id="dirs_x2"),
        pytest.param([SAMPLES_A.empty, SAMPLES_A.partial, SAMPLES_B.dirpath], id="files_x2+dir_x1"),
        pytest.param([os.path.join("sample_files", "subdir_a")], id="rel_dir_x1"),
    ],
)
@pytest.mark.parametrize(
    ["config_flag", "use_yml_ignore"],
    [
        pytest.param([], False, id="no_config_specified"),
        pytest.param(
            ["-C", os.path.join("config_files", "with_ignore.yml")],
            True,
            id="short_config_specifier_w_ignore",
        ),
        pytest.param(
            ["--config", os.path.join("config_files", "with_ignore.yml")],
            True,
            id="long_config_specifier_w_ignore",
        ),
        pytest.param(
            ["-C", os.path.join("config_files", "without_ignore.yml")],
            False,
            id="short_config_specifier_wo_ignore",
        ),
        pytest.param(
            ["--config", os.path.join("config_files", "without_ignore.yml")],
            False,
            id="long_config_specifier_wo_ignore",
        ),
    ],
)
@pytest.mark.parametrize(
    ["ignore_file_flag", "use_ignore_file"],
    [
        pytest.param([], False, id="no_ignore_file"),
        pytest.param(
            ["-d", os.path.join("config_files", "docstr_ignore.txt")], True, id="short_ignore_file"
        ),
        pytest.param(
            ["--docstr-ignore-file", os.path.join("config_files", "docstr_ignore.txt")],
            True,
            id="long_ignore_file",
        ),
    ],
)
@pytest.mark.usefixtures("cd_tests_dir_fixture")
@pytest.mark.skipif(
    sys.version_info < (3, 6), reason="assert_called_once requires python3.6 or later "
)
def test_ignore_patterns_files(
    paths: List[str],
    config_flag: List[str],
    use_yml_ignore: bool,
    ignore_file_flag: List[str],
    use_ignore_file: bool,
    runner: CliRunner,
    mocker,
):
    """Test that CLI inputs are correctly interpreted and passed along to
    :func:`docstr_coverage.cli.collect_filepaths`

    Parameters
    ----------
    paths: List[str]
        Path arguments provided to CLI. These should be made absolute before they are passed to
        :func:`docstr_coverage.cli.collect_filepaths`
    config_flag: List[str]
        CLI option to specify path of yml config file
    use_yml_ignore: Boolean
        True iff `config_flag` points to a file with custom ignore patterns
    ignore_file_flag: List[str]
        CLI option to specify path of a plain ignore patterns file
    use_ignore_file: Boolean
        True iff `ignore_file_flag` points to a file with custom ignore patterns
    runner: CliRunner
        Click utility to invoke command line scripts
    mocker: pytest_mock.MockFixture
        Mock to check arguments passed to :func:`docstr_coverage.cli.collect_filepaths`"""

    # Check that there is no `.docstr_coverage` file added to the test folder,
    #   which may be used as default
    assert not os.path.isfile(".docstr_coverage") and not os.path.isfile(
        ".docstr.yaml"
    ), "This test must run in a folder without config or ignore files"

    mock_parse_ig_f = mocker.patch("docstr_coverage.cli.parse_ignore_names_file")
    parse_ig_from_dict = mocker.patch("docstr_coverage.cli.parse_ignore_patterns_from_dict")

    run_result = runner.invoke(execute, paths + config_flag + ignore_file_flag)

    if use_yml_ignore and use_ignore_file:
        assert (
            run_result.exception
        ), "No exception was raised even though yml and txt custom ignore patterns were passed"
        assert isinstance(run_result.exception, ValueError)
        assert (
            "Ignore patterns must be specified in only one location at a time."
            in run_result.exception.args[0]
        )

    elif use_yml_ignore:
        mock_parse_ig_f.assert_not_called()
        parse_ig_from_dict.assert_called_once()
    elif use_ignore_file:
        parse_ig_from_dict.assert_not_called()
        mock_parse_ig_f.assert_called_once()
    else:
        parse_ig_from_dict.assert_not_called()
        mock_parse_ig_f.assert_not_called()


@pytest.mark.parametrize(
    ["paths", "path_contains_py"],
    [
        pytest.param([SAMPLES_DIR], True, id="samples_dir_x1"),
        pytest.param([SAMPLES_A.documented], True, id="files_x1"),
        pytest.param([SAMPLES_A.empty, SAMPLES_A.partial], True, id="files_x2"),
        pytest.param([SAMPLES_A.dirpath, SAMPLES_B.dirpath], True, id="dirs_x2"),
        pytest.param(
            [SAMPLES_A.empty, SAMPLES_A.partial, SAMPLES_B.dirpath], True, id="files_x2+dir_x1"
        ),
        pytest.param([os.path.join("sample_files", "subdir_a")], True, id="rel_dir_x1"),
        pytest.param(
            [os.path.join("config_files", "docstr_ignore.txt")], False, id="file_with_no_python"
        ),
        pytest.param([os.path.join(CWD, "config_files")], False, id="folder_with_no_python"),
    ],
)
@pytest.mark.parametrize(
    ["accept_empty_flag", "accept_empty_value"],
    [
        pytest.param([], False, id="no_accept_empty"),
        pytest.param(["-a"], True, id="short_accept_empty"),
        pytest.param(["--accept-empty"], True, id="long_accept_empty"),
    ],
)
@pytest.mark.usefixtures("cd_tests_dir_fixture")
def test_accept_empty(
    paths: List[str],
    path_contains_py: bool,
    accept_empty_flag: List[str],
    accept_empty_value: bool,
    runner: CliRunner,
):
    """ Test that the flag to accept paths
     which do not point to any .py file leads to the correct exit codes.

    Parameters
    ----------
    paths: List[str]
        Path arguments provided to CLI. These should be made absolute before they are passed to
        :func:`docstr_coverage.cli.collect_filepaths`
    path_contains_py: bool
        True iff the passed paths point (directly or indirectly via dir) to at least one .py file
    accept_empty_flag: List[str]
        Flag under test
    accept_empty_value: bool
        True iff the flag under test specifies to return exit code 0 if no .py file was found
    runner: CliRunner
        Click utility to invoke command line scripts"""

    dont_fail_due_to_coverage = ["--fail-under=5"]

    run_result = runner.invoke(execute, paths + accept_empty_flag + dont_fail_due_to_coverage)

    if accept_empty_flag or path_contains_py:
        assert run_result.exit_code == 0
    else:
        assert run_result.exit_code == 1
