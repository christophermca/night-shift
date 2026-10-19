import io
import pytest
from unittest.mock import Mock, patch, MagicMock, create_autospec
import subprocess
import requests
from gi.repository import Gio, GLib
from night_shift.bin.settings import Settings
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset

REAL_POPEN = subprocess.Popen
AGENT_CMD = ["/usr/lib/geoclue-2.0/demos/agent"]
WHERE_AM_I_CMD = [
    "/usr/lib/geoclue-2.0/demos/where-am-i",
    "--accuracy-level=8",
    "--time-threshold=3",
]

# What geoclue's where-am-i actually prints (note the trailing degree signs).
WHERE_AM_I_OUTPUT = """\
Client object: /org/freedesktop/GeoClue2/Client/1
New location:
Latitude:    40.712800°
Longitude:   -74.006000°
Accuracy:    50.000000 meters
Timestamp:   Mon 13 Oct 2026 09:00:00 AM EDT (1791896400 seconds since the Epoch)
"""


def fake_process(output=""):
    """A Popen-shaped fake. Real Popen sets .stdout in __init__, so autospec
    can't see it; give it a real text stream that returns "" at EOF."""
    proc = create_autospec(REAL_POPEN, instance=True)
    proc.stdout = io.StringIO(output)
    return proc


@pytest.fixture
def popen():
    with patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen") as popen:
        yield popen


@pytest.fixture
def fake_settings():
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
    print("mock_store_defaults: ", store)
    mock_settings.data_store = store  # so tests can check what was saved

    return mock_settings


@pytest.fixture
def fetcher(fake_settings):
    # With no settings, __init__ finds no static location and fetches nothing.
    fetcher = GetTimeOfSunriseSunset()
    fetcher.settings = fake_settings
    return fetcher


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
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
@patch("night_shift.bin.get_sunrise_sunset.requests.get")
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
            settings=self.settings,
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
            settings=self.settings,
        )

        assert object.use_geoclue == None
        assert object.times == None

    def test_calling_function(self, requests, mock_get_location):
        use_geoclue = None
        override = False
        verbose = 0
        lat = 40.7128
        lng = -74.0060

        requests.return_value = _mock_response(API_PAYLOAD)
        # mock_get_location.return_value = (lat, lng)  # NYC coordinates
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=self.settings,
        )

        sunrise_sunset([lat, lng])


class TestGetSunriseSunsetGetLocation:
    def _run(self, fetcher, popen, output=WHERE_AM_I_OUTPUT):
        agent, where_am_i = fake_process(), fake_process(output)
        popen.side_effect = [
            agent,
            where_am_i,
        ]  # 1st Popen() = agent, 2nd = where-am-i

        return fetcher._get_location(), agent, where_am_i

    def test_starts_the_agent_then_where_am_i(self, fetcher, popen):
        self._run(fetcher, popen)

        assert [c.args[0] for c in popen.call_args_list] == [
            AGENT_CMD,
            WHERE_AM_I_CMD,
        ]


@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
@patch("night_shift.bin.get_sunrise_sunset.requests.get")
class TestSettingsIsSet:

    def test_when_geoclue_is_None_and_settings_is_set(
        self, requests, mock_get_location, fake_settings
    ):
        use_geoclue = None
        override = False
        verbose = 0

        requests.return_value = _mock_response(API_PAYLOAD)

        object = GetTimeOfSunriseSunset(
            verbose=verbose,
            override=override,
            use_geoclue=use_geoclue,
            settings=fake_settings,
        )

        print("myobject", object.times)
        assert object.use_geoclue is False

        # fetched the times and saved them back to settings
        assert fake_settings.data_store["times"] == GLib.Variant(
            "(ss)", ("06:52", "18:51")
        )
        assert fake_settings.data_store["tzid"] == "America/New_York"


@patch("night_shift.bin.get_sunrise_sunset.requests.get")
def test_http_errors_are_reported_as_http_errors(mock_get, fetcher, capsys):
    mock_get.return_value.raise_for_status.side_effect = (
        requests.exceptions.HTTPError("500 Server Error")
    )

    assert fetcher._get_sunrise_sunset(40.7, -74.0, 0) is None
    assert "HTTP error occurred" in capsys.readouterr().out
