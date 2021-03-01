"""This module is for conf file .docstr.yaml"""
import os
from typing import Any, Callable, Dict, List

import click
import yaml


def set_config_defaults(ctx, param, value):
    """Update CLI option defaults in `ctx` to config file values

    Parameters
    ----------
    ctx: click.Context
        Click Context object
    param: click.Parameter
        Click Parameter object (assumed to be `config`)
    value: String
        Path to the configuration file

    Returns
    -------
    String
        Path to the configuration file"""
    if value is not None and os.path.exists(value):
        with open(value) as f:
            config_data = yaml.safe_load(f) or {}
            ctx.params["config_file"] = value
        # Resolve paths like Click would have with the `click.Path.resolve_path` kwarg
        _extract_non_default_list(
            config_data,
            ctx,
            "paths",
            lambda config_paths: tuple([os.path.realpath(path) for path in config_paths]),
        )
        _extract_non_default_list(config_data, ctx, "ignore_patterns", lambda x: x)
        # TODO This can be removed as part PR #52 (verbose counting).
        #       Until then, this is for compatibility with docs
        #       which require verbose in config-file to be an int
        if "verbose" in config_data:
            config_data["verbose"] = str(config_data["verbose"])
        ctx.default_map = config_data

    return value


def _extract_non_default_list(
    config_data: Dict, ctx: click.Context, field: str, process: Callable[[List], Any]
) -> None:
    """Processes a field of the config file which should be used as the default value
    if not provided as a CLI argument

    The field is considered an optional list: If not present in the config data,
    calling this method has no effect.
    If a single value (as opposed to a list) is present in `config_data` for this field,
    a list based on only this value will be appended to the ctx.params.

    Parameters
    ----------
    config_data: Dict
        Parsed yaml config file
    ctx: click.Context
        Click Context object
    field: str
        Name of the field for which the value has to be extracted
    process: Callable
        A mapping function, allowing to modify or replace transfer the values
        present in the config file before storing them in ctx.params"""
    try:
        # Check if `field` was given in config file
        config_paths = config_data.pop(field)
    except KeyError:
        # No value for field was provided
        pass
    else:
        # Use config default if `field` was not provided as CLI argument
        if not ctx.params.get(field) and config_paths:
            if isinstance(config_paths, str):
                config_paths = [config_paths]
            ctx.params[field] = process(config_paths)
