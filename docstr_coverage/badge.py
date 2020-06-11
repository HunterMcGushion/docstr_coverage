"""Module for creating docstring coverage badges.

Notes
-----
This module is based on the excellent [coverage-badge](https://github.com/dbrgn/coverage-badge)
repository. Thank you to the authors for their fantastic work! Go give
[coverage-badge](https://github.com/dbrgn/coverage-badge) a star!"""

import os
import pkg_resources


COLORS = {
    "brightgreen": "#4c1",
    "green": "#97CA00",
    "yellowgreen": "#a4a61d",
    "yellow": "#dfb317",
    "orange": "#fe7d37",
    "red": "#e05d44",
    "lightgrey": "#9f9f9f",
}

COLOR_RANGES = [
    (95, "brightgreen"),
    (90, "green"),
    (75, "yellowgreen"),
    (60, "yellow"),
    (40, "orange"),
    (0, "red"),
]


class Badge:
    def __init__(self, path: str, coverage: float):
        """Class to build and save a coverage badge based on `coverage` results

        Parameters
        ----------
        path: String
            File or directory path to which the coverage badge SVG should be saved. If `path` is a
            directory, the badge will be saved under the filename "docstr_coverage_badge.svg"
        coverage: Float
            Docstring coverage percentage"""
        self.path = path
        self.coverage = round(coverage)

        self._color = None
        self._badge = None

    #################### Properties ####################
    @property
    def path(self) -> str:
        """String: Filepath to which the coverage badge SVG should be saved. If set to a directory,
        "docstr_coverage_badge.svg" will be appended"""
        return self._path

    @path.setter
    def path(self, value: str):
        if os.path.isdir(value):
            value = os.path.join(value, "docstr_coverage_badge.svg")
        if not value.endswith(".svg"):
            value += ".svg"
        self._path = value

    @property
    def color(self) -> str:
        """String: Hex color code to use for badge based on :attr:`coverage`"""
        if self._color is None:
            for (minimum, color) in COLOR_RANGES:
                if self.coverage >= minimum:
                    self._color = COLORS[color]
                    break
            else:
                self._color = COLORS["lightgrey"]
        return self._color

    @property
    def badge(self) -> str:
        """String: SVG badge contents"""
        if self._badge is None:
            value = "{:.0f}".format(self.coverage)
            template_path = os.path.join("templates", "flat.svg")
            template = pkg_resources.resource_string(__name__, template_path).decode("utf8")
            self._badge = template.replace("{{ value }}", value).replace("{{ color }}", self.color)
        return self._badge

    #################### Core Methods ####################
    def save(self) -> str:
        """Save :attr:`badge` to :attr:`path`

        Returns
        -------
        path: String
            Full filepath to which the badge SVG is saved"""
        with open(self.path, "w") as f:
            f.write(self.badge)
        return self.path
