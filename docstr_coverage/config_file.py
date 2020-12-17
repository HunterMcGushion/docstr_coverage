"""
This module is for conf file .docstr.yaml
"""
import os

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
    if (value is not None) and os.path.exists(value):
        with open(value) as f:
            config_data = yaml.safe_load(f) or {}

        try:
            # Check if `paths` were given in config file
            config_paths = config_data.pop("paths")
        except KeyError:
            pass
        else:
            # Use config default if `paths` was not provided as CLI argument
            if (not ctx.params.get("paths")) and config_paths:
                if isinstance(config_paths, str):
                    config_paths = [config_paths]

                # Resolve paths like Click would have with the `click.Path.resolve_path` kwarg
                ctx.params["paths"] = tuple([os.path.realpath(path) for path in config_paths])
        finally:
            ctx.default_map = config_data

    return value
