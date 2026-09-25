import pytest
from datetime import datetime

from unittest.mock import Mock, patch, MagicMock
from night_shift.bin.is_day_or_night import is_day_or_night


@pytest.fixture(autouse=True)
def mock_settings():
    """Mock Gio.Settings object"""
    settings = MagicMock()
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_day(mock_settings_func, mock_settings):
    """Test detection of daytime"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunrise(mock_settings_func, mock_settings):
    """Test detection night before sunrise"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "05:59"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunrise(mock_settings_func, mock_settings):
    """Test detection transition at sunrise"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "06:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunset(mock_settings_func, mock_settings):
    """Test detection of daytime before sunset"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:29"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunset(mock_settings_func, mock_settings):
    """Test detection of transition at sunset"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:30"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_night(mock_settings_func, mock_settings):
    """Test detection of nighttime"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night.Gio.Settings.new_full")
def test_settings(mock_new_full):
    from night_shift.bin import is_day_or_night as module

    settings = module.Settings

    assert settings is mock_new_full.return_value

    schema_obj = mock_new_full.call_args.args[0]
    assert schema_obj.get_id() == "org.gnome.shell.extensions.night-shift"
