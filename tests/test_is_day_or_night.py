import pytest

from unittest.mock import patch, MagicMock
from night_shift.bin.is_day_or_night import is_day_or_night


@pytest.fixture()
def mock_settings():
    """Mock Gio.Settings object"""
    settings = MagicMock()
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_day(mock_settings_func, mock_settings):
    """Test detection of daytime"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunrise(mock_settings_func, mock_settings):
    """Test detection night before sunrise"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "05:59"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunrise(mock_settings_func, mock_settings):
    """Test detection transition at sunrise"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "06:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunset(mock_settings_func, mock_settings):
    """Test detection of daytime before sunset"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:29"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunset(mock_settings_func, mock_settings):
    """Test detection of transition at sunset"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:30"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_night(mock_settings_func, mock_settings):
    """Test detection of nighttime"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")
