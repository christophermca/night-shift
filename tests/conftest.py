import gi
import pytest
from unittest.mock import patch, MagicMock

gi.require_version("GLib", "2.0")
from gi.repository import GLib  # noqa: E402


@pytest.fixture(autouse=True)
def _patch_settings(mock_settings):
    with patch(
        "night_shift.bin.get_sunrise_sunset.Settings"
    ) as mock_settings_class:
        mock_settings_class.return_value.return_value = mock_settings
        yield mock_settings_class


@pytest.fixture
def mock_settings():
    """Mock Gio.Settings object"""
    settings = MagicMock()
    settings.get_string.return_value = ""
    settings.get_boolean.return_value = (
        False  # defaults to using "static location"
    )
    # Real Gio.Settings.get_value returns a GLib.Variant, not a tuple.
    settings.get_value.return_value = GLib.Variant("(dd)", (0.0, 0.0))
    return settings


@pytest.fixture
def fake_where_am_i():
    def make(lines):
        proc = MagicMock()
        proc.stdout.readline.side_effect = [*lines, ""]
        return proc

    return make
