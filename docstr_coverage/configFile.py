"""
This module is for conf file .docstr.yaml
"""
import os

import yaml


def readConfigFile(paths, kwargs):
    """
    Read config file and assign all variable to paths, kwargs.

    :param tuple paths: paths list
    :param dict kwargs: options

    :return (paths, kwargs)
    :rtype (tuple, dict)
    """
    # if .docstr.yaml not present return initial paths, and kwargs
    if not os.path.exists(".docstr.yaml"):
        return paths, kwargs

    with open(".docstr.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
            for item in config.keys():
                if item == "paths":
                    # yaml paths type list liek this:
                    # paths:
                    #     - docstr_coverage
                    #     - test
                    if type(config["paths"]) == list:
                        paths = tuple(config["paths"])
                    # or yaml paths type str like this:
                    # paths:  docstr_coverage
                    else:
                        paths = (config["paths"],)
                if item in kwargs.keys():
                    kwargs[item] = config[item]
            return paths, kwargs
        # if .docstr.yaml is not valid return initial paths, and kwargs
        except yaml.YAMLError:
            return paths, kwargs
