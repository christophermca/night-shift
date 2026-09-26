import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def _patch_settings(mock_settings):
    """Prevent GetTimeOfSunriseSunset.__init__ from touching real GSettings.

    `Settings()` is instantiated unconditionally in __init__, and its
    __init__ reaches out to the real (compiled) GNOME schema on disk.
    Patch the class so `self.settings()` resolves to `mock_settings`,
    matching Settings.__call__'s behavior.
    """
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
    settings.get_value.return_value = (0.0, 0.0)
    return settings
