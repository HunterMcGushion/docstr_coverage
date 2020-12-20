import os

import click
import pytest
import yaml

from docstr_coverage.config_file import set_config_defaults

TEST_CONFIG_FILE = ".docstr.yaml"

fake_config_file = {
    "paths": ["tests", "docstr_coverage"],
    "verbose": "2",
    "skip_magic": True,
    "skip_file_doc": True,
    "skip_init": True,
    "skip_class_def": True,
    "skip_private": True,
    "follow_links": True,
    "fail_under": 90,
    "percentage_only": True,
}
fake_config_file_string_paths = {
    "paths": "docstr_coverage",
    "verbose": "2",
    "skip_magic": True,
    "skip_file_doc": True,
    "skip_init": True,
    "skip_class_def": True,
    "skip_private": True,
    "follow_links": True,
    "fail_under": 90,
    "percentage_only": True,
}
fake_config_file_ignore_patterns = fake_config_file.copy()
test_ignore_patterns = {
    "SomeFile": ["method_to_ignore1", "method_to_ignore2", "method_to_ignore3"],
    "FileWhereWeWantToIgnoreAllSpecialMethods": "__.+__",
    ".*": "method_to_ignore_in_all_files",
    "a_very_important_view_file": ["^get$", "^set$", "^post$"],
    "detect_.*": ["get_val.*"],
}
fake_config_file_ignore_patterns["ignore_patterns"] = test_ignore_patterns


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    """
    Delete the fake config file before and after every test
    to make sure the tests do influence each other.
    """
    if os.path.isfile(TEST_CONFIG_FILE):
        os.remove(TEST_CONFIG_FILE)
    yield  # this is where the testing happens
    if os.path.isfile(TEST_CONFIG_FILE):
        os.remove(TEST_CONFIG_FILE)


def test_set_config_defaults_no_conf_file():
    """
    Test set_config_defaults when .docstr.yaml is missing
    """
    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), None)
    assert value is None
    assert ctx.params == {"paths": ()}


def test_set_config_defaults():
    """
    Test ReadConfigFile with fake .docstr.yaml with multiple paths
    """
    # fake .docstr.yaml
    with open(TEST_CONFIG_FILE, "w") as outfile:
        yaml.dump(fake_config_file, outfile, default_flow_style=False)

    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), ".docstr.yaml")
    outfile.close()
    # delete paths key
    del fake_config_file["paths"]

    assert ".docstr.yaml" in value
    assert type(ctx.params["paths"]) == tuple
    assert "test" in ctx.params["paths"][0]
    assert "docstr_coverage" in ctx.params["paths"][1]
    assert ctx.default_map.keys() == fake_config_file.keys()
    assert ctx.default_map["verbose"] == fake_config_file["verbose"]


def test_set_config_defaults_with_string_paths():
    """
    Test ReadConfigFile with fake .docstr.yaml with only one path
    """
    # fake .docstr.yaml
    with open(TEST_CONFIG_FILE, "w") as outfile:
        yaml.dump(fake_config_file_string_paths, outfile, default_flow_style=False)

    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), ".docstr.yaml")
    outfile.close()

    # delete paths key
    del fake_config_file_string_paths["paths"]

    assert ".docstr.yaml" in value
    assert type(ctx.params["paths"]) == tuple
    assert "docstr_coverage" in ctx.params["paths"][0]
    assert ctx.default_map.keys() == fake_config_file_string_paths.keys()
    assert ctx.default_map["verbose"] == fake_config_file_string_paths["verbose"]


def test_set_config_defaults_with_ignore_patterns():
    """
    Test ReadConfigFile with fake .docstr.yaml w.r.t. the parsing of custom ignore patterns
    """
    # fake .docstr.yaml
    with open(TEST_CONFIG_FILE, "w") as outfile:
        yaml.dump(fake_config_file_ignore_patterns, outfile, default_flow_style=False)

    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), ".docstr.yaml")
    outfile.close()

    # delete paths key
    del fake_config_file_ignore_patterns["paths"]
    del fake_config_file_ignore_patterns["ignore_patterns"]

    assert ".docstr.yaml" in value
    assert type(ctx.params["paths"]) == tuple
    assert "docstr_coverage" in ctx.params["paths"][0]
    assert ctx.default_map.keys() == fake_config_file_ignore_patterns.keys()
    assert ctx.default_map["verbose"] == fake_config_file_ignore_patterns["verbose"]
    assert ctx.params['ignore_patterns'] == test_ignore_patterns
