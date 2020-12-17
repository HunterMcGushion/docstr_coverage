import os
from unittest import TestCase

import click
import yaml

from docstr_coverage.config_file import set_config_defaults

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
    with open(".docstr.yaml", "w") as outfile:
        yaml.dump(fake_config_file, outfile, default_flow_style=False)

    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), ".docstr.yaml")
    outfile.close()
    # remove fake file
    os.remove(".docstr.yaml")
    # delete paths key
    fake_config_file_without_paths = fake_config_file
    del fake_config_file_without_paths["paths"]

    assert ".docstr.yaml" in value
    assert type(ctx.params["paths"]) == tuple
    assert "test" in ctx.params["paths"][0]
    assert "docstr_coverage" in ctx.params["paths"][1]
    assert ctx.default_map.keys() == fake_config_file_without_paths.keys()
    assert ctx.default_map["verbose"] == fake_config_file_without_paths["verbose"]


def test_set_config_defaults_with_string_paths():
    """
    Test ReadConfigFile with fake .docstr.yaml with only one path
    """
    # fake .docstr.yaml
    with open(".docstr.yaml", "w") as outfile:
        yaml.dump(fake_config_file_string_paths, outfile, default_flow_style=False)

    ctx = click.Context(click.Command("paths"))
    ctx.params = {"paths": ()}
    value = set_config_defaults(ctx, click.Option("-C", "--config"), ".docstr.yaml")
    outfile.close()
    # remove fake file
    os.remove(".docstr.yaml")

    # delete paths key
    fake_config_file_without_paths = fake_config_file_string_paths
    del fake_config_file_without_paths["paths"]

    assert ".docstr.yaml" in value
    assert type(ctx.params["paths"]) == tuple
    assert "docstr_coverage" in ctx.params["paths"][0]
    assert ctx.default_map.keys() == fake_config_file_without_paths.keys()
    assert ctx.default_map["verbose"] == fake_config_file_without_paths["verbose"]
