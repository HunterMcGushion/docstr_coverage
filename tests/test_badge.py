"""Tests for :mod:`docstr_coverage.badge`"""
import os

import pytest

from docstr_coverage.badge import Badge

CWD = os.path.abspath(os.path.dirname(__file__))
SAMPLE_BADGE_DIR = os.path.join(CWD, "sample_files", "badges")


def _clear_whitespace(string):
    return "".join(string.split())


@pytest.mark.parametrize(
    ["given_path", "expected"], [("foo/bar.svg", "foo/bar.svg"), ("foo", "foo.svg")]
)
def test_badge_path(given_path, expected):
    """Test that :attr:`docstr_coverage.badge.Badge.path` is set correctly when given paths to both
    files and directories"""
    b = Badge(given_path, 100)
    assert b.path == expected


@pytest.mark.parametrize(
    ["coverage", "expected"],
    [
        (100, "#4c1"),
        (97.5, "#4c1"),
        (95, "#4c1"),
        (91.9, "#97CA00"),
        (90, "#97CA00"),
        (83.6, "#a4a61d"),
        (75, "#a4a61d"),
        (74.9, "#a4a61d"),
        (74.3, "#dfb317"),
        (62.4, "#dfb317"),
        (60, "#dfb317"),
        (51.1, "#fe7d37"),
        (40, "#fe7d37"),
        (1.3, "#e05d44"),
        (0, "#e05d44"),
        (-32.32, "#9f9f9f"),
    ],
)
def test_badge_color(coverage, expected):
    """Test that :attr:`docstr_coverage.badge.Badge.color` is correct according to `coverage`"""
    b = Badge(".", coverage)
    assert b.color == expected


@pytest.mark.parametrize(
    ["coverage", "expected_filename"],
    [
        (100, "100.svg"),
        (94.2, "94.svg"),
        (83.5, "84.svg"),
        (70.9, "71.svg"),
        (54.3, "54.svg"),
        (12, "12.svg"),
        (0.1, "0.svg"),
    ],
)
def test_badge_contents(coverage, expected_filename):
    """Test that stringified badge (:attr:`docstr_coverage.badge.Badge.badge`) is correct before
    saving SVG file"""
    b = Badge(".", coverage)
    with open(os.path.join(SAMPLE_BADGE_DIR, expected_filename), "r") as f:
        assert _clear_whitespace(b.badge) == _clear_whitespace(f.read())


@pytest.mark.parametrize(["given_path", "coverage"], [("foo/bar.svg", 90)])
def test_badge_save(given_path, coverage, mocker):
    """Test that :meth:`docstr_coverage.badge.Badge.save` opens the expected filepath and writes the
    correct badge contents to the expected location"""
    mock_open = mocker.patch("docstr_coverage.badge.open", mocker.mock_open())

    b = Badge(given_path, coverage)
    b.save()
    mock_open.assert_called_once_with(b.path, "w")
    mock_open().write.assert_called_once_with(b.badge)
