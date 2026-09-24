import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset


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


@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
)
@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
class TestGetSunriseSunset:
    def test_get_sunrise_sunset_init(
        self, mock_get_api, mock_get_location, mock_settings
    ):
        object = GetTimeOfSunriseSunset(
            verbose=True, use_geoclue=True, override=True
        )

        assert object.verbose is True
        assert object.use_geoclue is True
        assert object.override is True

    def test_get_sunrise_sunset__call(
        self, mock_get_api, mock_get_location, mock_settings
    ):
        coords = (40.7128, -74.0060)  # NYC coordinates
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose=False, use_geoclue=True
        )
        sunrise_sunset(coords)

    def test_get_sunrise_sunset_times_success(
        self, mock_get_api, mock_get_location, mock_settings
    ):
        """Test successful sunrise/sunset fetch"""
        mock_get_location.return_value = (40.7128, -74.0060)  # NYC coordinates

        GetTimeOfSunriseSunset(use_geoclue=True)

        mock_get_api.assert_called_once_with(40.7128, -74.0060, False)
        # mock_get_api.assert_called_once_with(40.7128, -74.0060, False)

    def test_get_location_override(self, mock_get_api, mock_settings):
        GetTimeOfSunriseSunset(verbose=False, use_geoclue=True, override=True)

    def test_get_sunrise_sunset_times_http_error(
        self, mock_get_api, mock_get, mock_settings
    ):
        """Test handling of HTTP errors"""
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP 500")

        GetTimeOfSunriseSunset(verbose=False, override=True)
