import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.bin.get_sunrise_sunset import GetTimeOfSunriseSunset


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


@patch("src.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location")
@patch("src.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset")
def test_get_sunrise_sunset_success(
    mock_get_api, mock_get_location, mock_settings
):
    """Test successful sunrise/sunset fetch"""
    mock_get_location.return_value = (40.7128, -74.0060)  # NYC coordinates

    GetTimeOfSunriseSunset(debug=False)

    # Verify API was called with coordinates
    mock_get_api.assert_called_once_with(40.7128, -74.0060, False)


@patch("src.bin.get_sunrise_sunset.requests.get")
def test_get_sunrise_sunset_http_error(mock_get):
    """Test handling of HTTP errors"""
    mock_get.side_effect = requests.exceptions.HTTPError("HTTP 500")

    GetTimeOfSunriseSunset(debug=False, override=True)
