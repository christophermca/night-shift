import pytest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import subprocess
import requests
from gi.repository import Gio, GLib
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


###
# Suggested code snippet by Claude Sonnet5
###
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


### END of suggested code snippet


@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
)
@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
class TestGetSunriseSunset:
    def test_get_sunrise_sunset_init(self, mock_get_location, mock_settings):
        object = GetTimeOfSunriseSunset(
            verbose=True, use_geoclue=True, override=True
        )

        assert object.verbose is True
        assert object.use_geoclue is True
        assert object.override is True

    def test_get_sunrise_sunset__call(self, mock_get_location, mock_settings):
        coords = (40.7128, -74.0060)  # NYC coordinates
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose=False, use_geoclue=True
        )
        sunrise_sunset(coords)

    def test_get_sunrise_sunset_times_success(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        """Test successful sunrise/sunset fetch"""
        mock_get_location.return_value = (40.7128, -74.0060)  # NYC coordinates

        GetTimeOfSunriseSunset(use_geoclue=True)

        mock_get_sunrise_sunset.assert_called_once_with(
            40.7128, -74.0060, False
        )

    def test_get_location_override(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        GetTimeOfSunriseSunset(verbose=False, use_geoclue=True, override=True)

    def test_get_sunrise_sunset_times_http_error(
        self, mock_get, mock_settings
    ):
        """Test handling of HTTP errors"""
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP 500")

        GetTimeOfSunriseSunset(verbose=False, override=True)


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


class TestFetchSunriseSunset:
    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_returns_hh_mm_times(self, mock_get, mock_settings):
        mock_get.return_value = _mock_response(API_PAYLOAD)

        times = GetTimeOfSunriseSunset()((40.7128, -74.0060))

        assert times == ("06:52", "18:51")

    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_passes_coordinates_to_api(self, mock_get, mock_settings):
        mock_get.return_value = _mock_response(API_PAYLOAD)

        GetTimeOfSunriseSunset()((40.7128, -74.0060))

        mock_get.assert_called_once_with(
            "https://api.sunrise-sunset.org/v2",
            {"lat": 40.7128, "lng": -74.0060},
        )

    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_saves_times_tzid_and_timestamp(self, mock_get, mock_settings):
        mock_get.return_value = _mock_response(API_PAYLOAD)

        GetTimeOfSunriseSunset()((40.7128, -74.0060))

        mock_settings.set_string.assert_any_call("tzid", "America/New_York")
        timestamp_calls = [
            c for c in mock_settings.set_string.call_args_list
            if c.args[0] == "timestamp"
        ]
        assert len(timestamp_calls) == 1

        key, variant = mock_settings.set_value.call_args.args
        assert key == "times"
        assert variant.get_type_string() == "(ss)"
        assert variant.unpack() == ("06:52", "18:51")

    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_http_error_returns_none_and_saves_nothing(
        self, mock_get, mock_settings
    ):
        response = MagicMock()
        response.raise_for_status.side_effect = (
            requests.exceptions.HTTPError("500 Server Error")
        )
        mock_get.return_value = response

        assert GetTimeOfSunriseSunset()((40.7128, -74.0060)) is None
        mock_settings.set_string.assert_not_called()
        mock_settings.set_value.assert_not_called()

    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_verbose_prints_response(self, mock_get, mock_settings, capsys):
        mock_get.return_value = _mock_response(API_PAYLOAD)

        GetTimeOfSunriseSunset(verbose=True)((40.7128, -74.0060))

        assert '"tzid": "America/New_York"' in capsys.readouterr().out


class TestStaticLocation:
    @patch(
        "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
    )
    def test_uses_static_coords_from_settings(
        self, mock_fetch, mock_settings
    ):
        mock_settings.get_string.side_effect = {
            "static-latitude": "51.5074",
            "static-longitude": "-0.1278",
        }.get

        GetTimeOfSunriseSunset()

        mock_fetch.assert_called_once_with(51.5074, -0.1278, False)
        key, variant = mock_settings.set_value.call_args.args
        assert key == "last-known-coordinates"
        assert variant.unpack() == (51.5074, -0.1278)

    @patch(
        "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
    )
    def test_missing_static_coords_skips_fetch(
        self, mock_fetch, mock_settings, capsys
    ):
        mock_settings.get_string.return_value = ""

        GetTimeOfSunriseSunset()

        mock_fetch.assert_not_called()
        assert "Missing required keys" in capsys.readouterr().out


class TestSave:
    def _instance(self):
        # No static coords in mock_settings, so __init__ makes no fetch.
        return GetTimeOfSunriseSunset()

    def test_dispatches_by_type(self, mock_settings):
        variant = GLib.Variant("(ss)", ("06:00", "18:00"))

        self._instance()._save({"name": "value", "count": 3, "times": variant})

        mock_settings.set_string.assert_called_once_with("name", "value")
        mock_settings.set_int.assert_called_once_with("count", 3)
        mock_settings.set_value.assert_called_once_with("times", variant)

    def test_swallows_errors(self, mock_settings, capsys):
        mock_settings.set_string.side_effect = RuntimeError("boom")

        self._instance()._save({"name": "value"})

        assert "ERROR SAVING boom" in capsys.readouterr().out

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: _save calls set_bool, but Gio.Settings only has set_boolean",
    )
    def test_bool_uses_real_gio_method(self, mock_settings):
        instance = self._instance()
        real_api = MagicMock(spec=Gio.Settings)
        instance.settings = lambda: real_api

        instance._save({"enabled": True})

        real_api.set_boolean.assert_called_once_with("enabled", True)


# Captured before any test patches subprocess.Popen.
REAL_POPEN = subprocess.Popen


def _fake_where_am_i(lines):
    proc = MagicMock()
    proc.stdout.readline.side_effect = [*lines, ""]
    return proc


class TestGeoclueLocation:
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_parses_lat_lng(self, mock_popen, mock_settings):
        agent = MagicMock()
        where_am_i = _fake_where_am_i(
            [
                "Client object: /org/freedesktop/GeoClue2/Client/1\n",
                "New location:\n",
                "Latitude:    40.712800\n",
                "Longitude:   -74.006000\n",
                "Accuracy:    50.000000 meters\n",
            ]
        )
        mock_popen.side_effect = [agent, where_am_i]
        instance = GetTimeOfSunriseSunset()

        assert instance._get_location() == (40.7128, -74.006)
        where_am_i.terminate.assert_called_once()

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_override_saves_last_known_coordinates(
        self, mock_popen, mock_settings
    ):
        mock_popen.side_effect = [
            MagicMock(),
            _fake_where_am_i(["Latitude: 1.5\n", "Longitude: 2.5\n"]),
        ]
        instance = GetTimeOfSunriseSunset(override=True)

        instance._get_location()

        key, variant = mock_settings.set_value.call_args.args
        assert key == "last-known-coordinates"
        assert variant.unpack() == (1.5, 2.5)

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_no_location_raises(self, mock_popen, mock_settings):
        mock_popen.side_effect = [MagicMock(), _fake_where_am_i(["nothing\n"])]
        instance = GetTimeOfSunriseSunset()

        with pytest.raises(TypeError, match="Could not determine location"):
            instance._get_location()

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_parses_real_where_am_i_format(self, mock_popen, mock_settings):
        mock_popen.side_effect = [
            MagicMock(),
            _fake_where_am_i(
                ["Latitude:    40.712800°\n", "Longitude:   -74.006000°\n"]
            ),
        ]

        assert GetTimeOfSunriseSunset()._get_location() == (40.7128, -74.006)

    @pytest.mark.xfail(
        strict=True,
        reason="BUG: cleanup checks callable(self.agent); a Popen is not callable, so the agent is never killed",
    )
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_kills_geoclue_agent(self, mock_popen, mock_settings):
        agent = create_autospec(REAL_POPEN, instance=True)
        agent.poll.return_value = 0
        mock_popen.side_effect = [
            agent,
            _fake_where_am_i(["Latitude: 1.5\n", "Longitude: 2.5\n"]),
        ]

        GetTimeOfSunriseSunset()._get_location()

        agent.kill.assert_called_once()
