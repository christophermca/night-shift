import pytest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import subprocess
import requests
from gi.repository import Gio, GLib
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset


@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
)
@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
class TestGetSunriseSunset:
    def test_get_sunrise_sunset_init(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        object = GetTimeOfSunriseSunset(
            verbose=True, use_geoclue=True, override=True
        )

        assert object.verbose is True
        assert object.use_geoclue is True
        assert object.override is True

    def test_get_sunrise_sunset__call(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        mock_get_location.return_value = None  # __init__ skips its own fetch
        sunrise_sunset = GetTimeOfSunriseSunset(use_geoclue=True)

        result = sunrise_sunset((40.7128, -74.0060), True)

        mock_get_sunrise_sunset.assert_called_once_with(
            40.7128, -74.0060, True
        )
        assert result is mock_get_sunrise_sunset.return_value

    def test_get_sunrise_sunset_times_success(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        """Test successful sunrise/sunset fetch"""
        mock_get_location.return_value = (40.7128, -74.0060)  # NYC coordinates

        GetTimeOfSunriseSunset(use_geoclue=True)

        mock_get_sunrise_sunset.assert_called_once_with(
            40.7128, -74.0060, False
        )

    def test_geoclue_on_uses_geoclue_location(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        GetTimeOfSunriseSunset(use_geoclue=True)

        mock_get_location.assert_called_once_with()
        mock_settings.get_string.assert_not_called()

    def test_geoclue_off_uses_static_location(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        mock_settings.get_string.side_effect = {
            "static-latitude": "51.5074",
            "static-longitude": "-0.1278",
        }.get

        GetTimeOfSunriseSunset(use_geoclue=False)

        mock_get_location.assert_not_called()
        mock_get_sunrise_sunset.assert_called_once_with(
            51.5074, -0.1278, False
        )

    def test_no_location_skips_fetch(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        mock_get_location.return_value = None

        GetTimeOfSunriseSunset(use_geoclue=True)

        mock_get_sunrise_sunset.assert_not_called()


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
            c
            for c in mock_settings.set_string.call_args_list
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
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
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
    def test_uses_static_coords_from_settings(self, mock_fetch, mock_settings):
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

    def test_bool_uses_real_gio_method(self, mock_settings):
        instance = self._instance()
        real_api = MagicMock(spec=Gio.Settings)
        instance.settings = lambda: real_api

        instance._save({"enabled": True})

        real_api.set_boolean.assert_called_once_with("enabled", True)


REAL_POPEN = subprocess.Popen


class TestGeoclueLocation:
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_parses_lat_lng(self, mock_popen, mock_settings, fake_where_am_i):
        agent = MagicMock()
        where_am_i = fake_where_am_i(
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

    @pytest.mark.parametrize(
        "saved, override, should_save",
        [
            ((1.5, 2.5), False, False),
            ((9.0, 9.0), False, True),
            ((1.5, 2.5), True, True),
        ],
        ids=["unchanged", "moved", "override"],
    )
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_saves_coordinates_only_when_needed(
        self,
        mock_popen,
        saved,
        override,
        should_save,
        mock_settings,
        fake_where_am_i,
    ):
        mock_settings.get_value.return_value = GLib.Variant("(dd)", saved)
        mock_popen.side_effect = [
            MagicMock(),
            fake_where_am_i(["Latitude: 1.5\n", "Longitude: 2.5\n"]),
        ]

        GetTimeOfSunriseSunset(override=override)._get_location()

        assert mock_settings.set_value.called is should_save

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_override_saves_last_known_coordinates(
        self, mock_popen, mock_settings, fake_where_am_i
    ):
        mock_popen.side_effect = [
            MagicMock(),
            fake_where_am_i(["Latitude: 1.5\n", "Longitude: 2.5\n"]),
        ]
        instance = GetTimeOfSunriseSunset(override=True)

        instance._get_location()

        key, variant = mock_settings.set_value.call_args.args
        assert key == "last-known-coordinates"
        assert variant.unpack() == (1.5, 2.5)

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_no_location_raises(
        self, mock_popen, mock_settings, fake_where_am_i
    ):
        mock_popen.side_effect = [MagicMock(), fake_where_am_i(["nothing\n"])]
        instance = GetTimeOfSunriseSunset()

        with pytest.raises(TypeError, match="Could not determine location"):
            instance._get_location()

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_parses_real_where_am_i_format(
        self, mock_popen, mock_settings, fake_where_am_i
    ):
        mock_popen.side_effect = [
            MagicMock(),
            fake_where_am_i(
                ["Latitude:    40.712800°\n", "Longitude:   -74.006000°\n"]
            ),
        ]

        assert GetTimeOfSunriseSunset()._get_location() == (40.7128, -74.006)

    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_kills_geoclue_agent(
        self, mock_popen, mock_settings, fake_where_am_i
    ):
        agent = create_autospec(REAL_POPEN, instance=True)
        agent.poll.return_value = 0
        mock_popen.side_effect = [
            agent,
            fake_where_am_i(["Latitude: 1.5\n", "Longitude: 2.5\n"]),
        ]

        GetTimeOfSunriseSunset()._get_location()

        agent.kill.assert_called_once()
        agent.wait.assert_called_once()

    @pytest.mark.parametrize(
        "error, message",
        [
            (subprocess.TimeoutExpired("where-am-i", 3), "TimeoutExpired: 3"),
            (subprocess.CalledProcessError(1, "where-am-i"), "Error: 1"),
        ],
        ids=["timeout", "process-error"],
    )
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_geoclue_failure_returns_none(
        self, mock_popen, error, message, mock_settings, capsys
    ):
        mock_popen.side_effect = [MagicMock(), error]
        instance = GetTimeOfSunriseSunset()

        assert instance._get_location() is None
        assert message in capsys.readouterr().out
        mock_settings.set_value.assert_not_called()
