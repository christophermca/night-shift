from unittest.mock import patch

import pytest


@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["nocturne-shift", *args])

    return set_args


@pytest.fixture
def mock_fetcher():
    with patch("nocturne_shift.cli.GetTimeOfSunriseSunset", autospec=True) as fetcher:
        yield fetcher


@pytest.fixture
def mock_check():
    with patch("nocturne_shift.cli.check") as check:
        yield check


@pytest.fixture(autouse=True)
def _no_real_settings():
    """The core CLI builds Settings/DataStore; fake them so nothing touches GSettings."""
    with patch("nocturne_shift.cli.Settings"), patch("nocturne_shift.cli.DataStore"):
        yield
