from unittest.mock import patch

import pytest


@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["night-shift", *args])

    return set_args


@pytest.fixture
def mock_fetcher():
    with patch("night_shift.cli.GetTimeOfSunriseSunset", autospec=True) as fetcher:
        yield fetcher


@pytest.fixture
def mock_check():
    with patch("night_shift.cli.check") as check:
        yield check


@pytest.fixture(autouse=True)
def _no_real_settings():
    """The core CLI builds Settings/DataStore; fake them so nothing touches GSettings."""
    with patch("night_shift.cli.Settings"), patch("night_shift.cli.DataStore"):
        yield
