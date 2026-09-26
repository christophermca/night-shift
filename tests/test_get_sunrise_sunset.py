# LEARN: Lesson 5, the advanced material. Read lessons 1-4 first.
#
# `GetTimeOfSunriseSunset` touches three outside systems: GSettings (via
# `Settings`), the HTTP API (via `requests`), and geoclue (via
# `subprocess.Popen`). Each test fakes whichever of those it isn't about.
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
    # LEARN: These defaults matter. With empty static coordinates,
    # `__init__` prints "Missing required keys" and does NOT fetch. That
    # gives most tests a quiet object to start from.
    settings.get_string.return_value = ""
    settings.get_boolean.return_value = (
        False  # defaults to using "static location"
    )
    settings.get_value.return_value = (0.0, 0.0)
    return settings


###
# Suggested code snippet by Claude Sonnet5
###
# LEARN: `autouse=True` means every test in this file uses this fixture
# without asking for it. It's Jest's top-level `beforeEach` or a JUnit
# `@BeforeEach` in a base class. Keep autouse for things that must ALWAYS
# happen, like "never touch the real GNOME settings". To share it across
# files, move it into `tests/conftest.py`, which pytest loads automatically
# (like Jest's `setupFilesAfterEnv`).
#
# How it works: `__init__` does `self.settings = Settings()`, and the code
# then calls `self.settings()` to get the Gio object. So:
#   Settings                            -> mock_settings_class (the class)
#   Settings()                          -> .return_value        (an instance)
#   Settings()()   i.e. self.settings() -> .return_value.return_value
# Setting that last one to `mock_settings` means the fixture above is
# exactly what the code sees, so tests can assert on it.
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


# LEARN: `@patch` on a *class* applies to every `test_*` method in it.
# That's handy, but it sets a trap worth studying:
#
# 1. Order. Stacked decorators apply bottom-up, so the BOTTOM patch
#    (`_get_location`) becomes the FIRST argument after `self`, and the top
#    one (`_get_sunrise_sunset`) becomes the second.
# 2. Every method receives BOTH mocks, whether it lists them or not. Python
#    passes them by position, and the parameter names don't matter. Only
#    after them do real fixtures get injected by name.
#
# So in `test_get_sunrise_sunset_init(self, mock_get_location, mock_settings)`
# below, `mock_settings` is NOT the fixture. It's the `_get_sunrise_sunset`
# mock under the wrong name. The test happens to pass because it never uses
# it. `test_get_sunrise_sunset_times_success` lists all three and gets them
# right. When a mock-argument test acts strangely, check this first.
@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_sunrise_sunset"
)
@patch(
    "night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset._get_location"
)
class TestGetSunriseSunset:
    # LEARN: Test classes just group related tests. There's no inheritance
    # needed, and they must NOT define `__init__` or pytest skips them. Each
    # test method gets a fresh instance, so don't try to share state
    # through `self`.
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

        # LEARN: This is testing the *wiring*: whatever `_get_location`
        # returns gets unpacked into `_get_sunrise_sunset`. Both methods
        # are mocked, so this proves `__init__` connects them properly
        # without running either one.
        mock_get_sunrise_sunset.assert_called_once_with(
            40.7128, -74.0060, False
        )

    def test_get_location_override(
        self, mock_get_location, mock_get_sunrise_sunset, mock_settings
    ):
        GetTimeOfSunriseSunset(verbose=False, use_geoclue=True, override=True)

    # LEARN: A test that can never fail. Worth studying:
    #   - `mock_get` is really the `_get_location` mock (the first positional
    #     argument, see the class comment), not `requests.get`.
    #   - `use_geoclue` defaults to False, so `_get_location` is never
    #     called, and its `side_effect` never fires.
    #   - `_get_sunrise_sunset` is mocked by the class decorator anyway, so
    #     no HTTP code runs at all.
    # It passes, but proves nothing about HTTP errors.
    # `TestFetchSunriseSunset.test_http_error_returns_none_and_saves_nothing`
    # below is the working version.
    #
    # Useful habit: break the code on purpose (make it raise, delete the
    # except) and check the test goes red. If it stays green, the test isn't
    # testing what you think.
    def test_get_sunrise_sunset_times_http_error(
        self, mock_get, mock_settings
    ):
        """Test handling of HTTP errors"""
        mock_get.side_effect = requests.exceptions.HTTPError("HTTP 500")

        GetTimeOfSunriseSunset(verbose=False, override=True)


# LEARN: A plain helper function (not a fixture) to build fake HTTP
# responses. Use a helper when tests need *different* data. Use a fixture
# when tests need the same setup or teardown.
def _mock_response(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    return response


# LEARN: A module-level constant for test data. Using a real-looking
# response (with a timezone offset) tests the parsing properly, where a
# neat made-up value might hide a bug.
API_PAYLOAD = {
    "sunrise": "2026-09-25T06:52:10-04:00",
    "sunset": "2026-09-25T18:51:30-04:00",
    "tzid": "America/New_York",
}


# LEARN: Unlike the class above, these tests do NOT mock
# `_get_sunrise_sunset`. They run the real method and mock only the
# network (`requests.get`). Mock at the outermost edge you can: the more
# real code a test runs, the more it proves.
class TestFetchSunriseSunset:
    # LEARN: Patch `requests.get` as get_sunrise_sunset.py sees it. The
    # module does `import requests` and then calls `requests.get(...)`, so
    # the target is `<module>.requests.get`.
    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_returns_hh_mm_times(self, mock_get, mock_settings):
        mock_get.return_value = _mock_response(API_PAYLOAD)

        # LEARN: `GetTimeOfSunriseSunset()` builds the object, and the second
        # `(...)` calls its `__call__` method. It's like calling a function
        # object in JS.
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
        # LEARN: The timestamp is "now", so we can't predict its value. We
        # assert it was saved exactly once and leave the value alone. Only
        # assert what the test can know for sure.
        timestamp_calls = [
            c
            for c in mock_settings.set_string.call_args_list
            if c.args[0] == "timestamp"
        ]
        assert len(timestamp_calls) == 1

        # LEARN: Tuple unpacking on `call_args.args`, where the positional
        # args are (key, value). Here the value is a real `GLib.Variant`
        # (only the settings store is fake), so we can check its GVariant
        # type string and unpack it back into Python values.
        key, variant = mock_settings.set_value.call_args.args
        assert key == "times"
        assert variant.get_type_string() == "(ss)"
        assert variant.unpack() == ("06:52", "18:51")

    @patch("night_shift.bin.get_sunrise_sunset.requests.get")
    def test_http_error_returns_none_and_saves_nothing(
        self, mock_get, mock_settings
    ):
        # LEARN: Put the error where the real one would come from:
        # `raise_for_status()` is what raises HTTPError on a 4xx/5xx. Making
        # `requests.get` itself raise would skip that line in the code.
        response = MagicMock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "500 Server Error"
        )
        mock_get.return_value = response

        assert GetTimeOfSunriseSunset()((40.7128, -74.0060)) is None
        mock_settings.set_string.assert_not_called()
        mock_settings.set_value.assert_not_called()

    # LEARN: `@patch` arguments come first, then fixtures (`mock_settings`,
    # `capsys`) by name. Mixing the two is fine as long as the patch
    # arguments go first.
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
        # LEARN: `side_effect` can also be a *function*, and then the mock
        # returns whatever that function returns for the same arguments.
        # Passing a dict's `.get` gives a lookup table: `get_string("static-latitude")`
        # returns "51.5074", and any other key returns None. This is
        # Mockito's `thenAnswer(...)` or Jest's `mockImplementation(key => table[key])`.
        mock_settings.get_string.side_effect = {
            "static-latitude": "51.5074",
            "static-longitude": "-0.1278",
        }.get

        GetTimeOfSunriseSunset()

        # LEARN: The strings come back as floats. The test proves the
        # conversion happens.
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
    # LEARN: A small helper method on the test class. It isn't collected as
    # a test because its name doesn't start with `test`.
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

    # LEARN: This test shows the biggest weakness of plain MagicMock: it
    # accepts ANY method name. The code calls `settings.set_bool(...)`, and
    # a plain MagicMock happily records it. The real `Gio.Settings` has no
    # `set_bool` (it's `set_boolean`), so the code breaks for real while
    # every loose-mock test passes.
    #
    # `MagicMock(spec=Gio.Settings)` restricts the mock to the real class's
    # attributes, so calling a method that doesn't exist raises
    # AttributeError, exactly like production would. Mockito gets this for
    # free because Java is type-checked. In Python you opt in with `spec`.
    # Use it at important boundaries.
    @pytest.mark.xfail(
        strict=True,
        reason="BUG: _save calls set_bool, but Gio.Settings only has set_boolean",
    )
    def test_bool_uses_real_gio_method(self, mock_settings):
        instance = self._instance()
        real_api = MagicMock(spec=Gio.Settings)
        # LEARN: Swap the dependency on this one instance. A `lambda` that
        # returns the spec'd mock stands in for the callable `Settings`
        # wrapper.
        instance.settings = lambda: real_api

        instance._save({"enabled": True})

        real_api.set_boolean.assert_called_once_with("enabled", True)


# LEARN: The tests below patch `subprocess.Popen`, and that patch hits the
# *shared* `subprocess` module, so while one is running, `subprocess.Popen`
# here is a mock too. Keeping a reference to the real class at import time
# (before any test runs) keeps it available for building a `spec` later.
# Captured before any test patches subprocess.Popen.
REAL_POPEN = subprocess.Popen


def _fake_where_am_i(lines):
    proc = MagicMock()
    # LEARN: `side_effect` set to a *list* returns the next item on each
    # call, like Mockito's `thenReturn(a, b, c)` or Jest's chained
    # `mockReturnValueOnce`. It fakes reading a process's output line by
    # line. The final "" is end-of-file, which stops the
    # `iter(readline, "")` loop in the code.
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
        # LEARN: The code calls `Popen` twice, first for the agent and then
        # for where-am-i. A list `side_effect` hands back a different fake
        # process for each call, in order.
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

        # LEARN: `match=` is a regex searched against the exception message.
        # It makes sure you caught the *right* TypeError, not some unrelated
        # one.
        with pytest.raises(TypeError, match="Could not determine location"):
            instance._get_location()

    # LEARN: A *regression test* built from real-world input. geoclue's
    # where-am-i prints a trailing "°". An earlier guess was that this broke
    # `float()`, so the test was first written as an xfail. It passed
    # unexpectedly (a strict XPASS), which showed the regex already stops
    # before the "°". strict xfail proved a hunch wrong, and this became a
    # normal test that guards that behavior.
    @patch("night_shift.bin.get_sunrise_sunset.subprocess.Popen")
    def test_parses_real_where_am_i_format(self, mock_popen, mock_settings):
        mock_popen.side_effect = [
            MagicMock(),
            _fake_where_am_i(
                ["Latitude:    40.712800°\n", "Longitude:   -74.006000°\n"]
            ),
        ]

        assert GetTimeOfSunriseSunset()._get_location() == (40.7128, -74.006)

    # LEARN: Another bug that only a `spec` catches. The cleanup code does
    # `if callable(self.agent): ... kill()`. A plain MagicMock IS callable,
    # so a loose mock would sail through the kill branch and the test would
    # pass. A real `Popen` object is NOT callable, so in production the
    # agent is never killed.
    #
    # `create_autospec(cls, instance=True)` builds a mock shaped like an
    # *instance* of the class: same methods and signatures, and not callable
    # unless the real instance is. (`MagicMock(spec=REAL_POPEN)` isn't enough:
    # a spec taken from a *class* is callable, because classes are.)
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
