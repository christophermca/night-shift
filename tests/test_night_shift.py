import pytest
import night_shift
from unittest.mock import Mock, patch, MagicMock
from night_shift.bin.is_day_or_night import is_day_or_night


@pytest.fixture()
def mock_settings():
    """Mock Gio.Settings object"""
    settings = MagicMock()
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


@patch("night_shift.bin.is_day_or_night.Settings")
def test_check(mock_settings_func, mock_settings):
    mock_settings_func.return_value.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        night_shift.check()
        mock_settings.set_string.assert_called_with("day-or-night", "day")
