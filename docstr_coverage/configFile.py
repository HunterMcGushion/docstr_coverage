"""
This module is for conf file .docstr.yaml
"""
import yaml


def readConfigFile(paths, **kwargs):
    """
    Read config file and assign all variable to paths, kwargs.
    """
    with open(".docstr.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            for item in config.keys():
                if item == "paths":
                    if type(config["paths"]) == list:
                        paths = tuple(config["paths"])
                    else:
                        paths = (config["paths"],)
                if item in kwargs.keys():
                    kwargs[item] = config[item]
            return paths, kwargs
        except yaml.YAMLError:
            return paths, kwargs
