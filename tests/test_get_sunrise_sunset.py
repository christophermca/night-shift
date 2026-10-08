import pytest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import subprocess
import requests
from gi.repository import Gio, GLib
from gnome_night_shift.bin.settings import Settings
from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset


@pytest.fixture
def settings():
    """A fake Settings backed by a dict: get() reads it, set() writes to it."""
    store = {
        "times": ("", ""),
        "use-geoclue": False,
        "static-latitude": "40.7128",
        "static-longitude": "-74.0060",
    }
    mock_settings = create_autospec(Settings, instance=True)
    mock_settings.get.side_effect = store.get
    mock_settings.set.side_effect = store.__setitem__
    mock_settings.store = store  # so tests can check what was saved

    return mock_settings


def _mock_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


API_PAYLOAD = {
    "sunrise": "2026-09-25T06:52:10-04:00",
    "sunset": "2026-09-25T18:51:30-04:00",
    "tzid": "America/New_York",
}


@patch(
    "gnome_night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
@patch("gnome_night_shift.bin.get_sunrise_sunset.requests.get")
class TestGetSunriseSunset:
    settings = None

    def test_when_geoclue_is_True_and_settings_is_None(
        self, requests, mock_get_location
    ):
        use_geoclue = True
        override = False
        verbose = 0
        lat = 22.0
        lng = -84.0

        requests.return_value = _mock_response(API_PAYLOAD)
        mock_get_location.return_value = (40.7128, -74.0060)  # NYC coordinates
        object = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=self.settings,
        )

        assert object.use_geoclue == True
        assert object.times == ("06:52", "18:51")

    def test_when_geoclue_is_False_and_settings_is_None(
        self, requests, mock_get_location
    ):
        use_geoclue = False
        override = False
        verbose = 0
        lat = 40.7128
        lng = -74.0060

        requests.return_value = _mock_response(API_PAYLOAD)
        mock_get_location.return_value = (lat, lng)  # NYC coordinates
        object = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=settings,
        )

        assert object.use_geoclue == False
        assert object.times == None

    def test_when_geoclue_is_None_and_settings_is_None(
        self, requests, mock_get_location
    ):
        use_geoclue = None
        override = False
        verbose = 0
        lat = 40.7128
        lng = -74.0060

        requests.return_value = _mock_response(API_PAYLOAD)
        mock_get_location.return_value = (lat, lng)  # NYC coordinates
        object = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=None,
        )

        assert object.use_geoclue == None
        assert object.times == None


@patch(
    "gnome_night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
@patch("gnome_night_shift.bin.get_sunrise_sunset.requests.get")
class TestGivenSettings:

    def test_when_geoclue_is_None_and_settings_is_set(
        self, requests, mock_get_location, settings
    ):
        use_geoclue = None
        override = False
        verbose = 0

        requests.return_value = _mock_response(API_PAYLOAD)

        object = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=settings,
        )

        print(settings)
        assert object.use_geoclue is False

        # fetched the times and saved them back to settings
        # assert settings.store["times"] == GLib.Variant(
        #     "(ss)", ("06:52", "18:51")
        # )
        assert settings.store["tzid"] == "America/New_York"
