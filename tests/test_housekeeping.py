"""Nonfunctional tests regarding manual configuration."""
import re


def test_version_consistency():
    """Tests that all version strings are consistent."""

    # Setup.py
    setup_version = "not-parsed"
    with open("setup.py", "r") as setup_file:
        for line in setup_file.readlines():
            if line.startswith("MAJOR, MINOR, MICRO"):
                setup_version = ".".join("".join(line.split()).split("=")[1].split(","))
                break
    # Documentation
    docs_version = "not-parsed"
    with open("docs/conf.py", "r") as setup_file:
        for line in setup_file.readlines():
            if line.startswith("release = "):
                docs_version = line.split('"')[1]
                break
    # Pre-Commit Example in README.md
    readme_hook_version = "not-parsed"
    with open("README.md", "r") as setup_file:
        for line in setup_file.readlines():
            # remove spaces
            line = "".join(line.split())
            if line.startswith("rev:v"):
                re_result = re.search("rev:v(.*)#mostrecent", line)
                readme_hook_version = re_result.group(1)
                break

    assert (
        setup_version == docs_version
    ), "version in docs ({}) does not match setup.py version ({})".format(
        docs_version, setup_version
    )
    assert (
        setup_version == readme_hook_version
    ), "version in readme ({}) does not match setup.py version ({})".format(
        readme_hook_version, setup_version
    )
