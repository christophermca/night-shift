import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.bin.is_day_or_night import is_day_or_night


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


@patch("src.bin.is_day_or_night._settings")
def test_is_day_or_night_during_day(mock_settings_func, mock_settings):
    """Test detection of daytime"""
    mock_settings_func.return_value = mock_settings

    with patch("src.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("src.bin.is_day_or_night._settings")
def test_is_day_or_night_during_night(mock_settings_func, mock_settings):
    """Test detection of nighttime"""
    mock_settings_func.return_value = mock_settings

    with patch("src.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")
