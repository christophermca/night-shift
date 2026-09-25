# LEARN: Lesson 1, the basics. Start here (see docs/testing-guide.md).
#
# pytest collects every `test_*.py` file in `tests/` (set in pytest.ini) and
# runs every function whose name starts with `test_`. There's no base class
# to extend or annotation to add, unlike JUnit's `@Test`. It works more like
# Jest picking up `*.test.js` files.
import pytest
from datetime import datetime

# LEARN: `unittest.mock` is part of the standard library, so there's nothing
# to install. It plays the role of Mockito in Java or `jest.fn()`/`jest.mock()`.
#   Mock      - a fake object. Any attribute you touch is created on the fly
#               as another Mock, and every call is recorded.
#   MagicMock - a Mock that also supports "magic" methods (`len()`,
#               iteration, `with`, ...). It's the safe default choice.
#   patch     - temporarily swaps a real name for a MagicMock and puts the
#               original back afterwards (like `jest.spyOn(...).mockImpl`
#               followed by `mockRestore()`).
from unittest.mock import Mock, patch, MagicMock
from night_shift.bin.is_day_or_night import is_day_or_night


# LEARN: A *fixture* is pytest's version of `beforeEach`. Instead of
# assigning to `this.x` in a setup hook, a test just names the fixture as a
# parameter and pytest injects the value. Each test gets a fresh one, so no
# state leaks between tests.
@pytest.fixture
def mock_settings():
    settings = MagicMock()
    # LEARN: `return_value` is what the mock returns when it's *called*.
    # This is Mockito's `when(settings.getValue(any())).thenReturn(...)` or
    # Jest's `mockReturnValue(...)`. Here it fakes the (sunrise, sunset)
    # pair that GSettings would normally store.
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


# LEARN: `@patch("a.b.c")` replaces the name `c` inside module `a.b` for the
# length of this test, and passes the replacement mock in as an argument.
#
# The #1 pytest/mock gotcha: patch the name where it's *looked up*, not
# where it's defined. `is_day_or_night()` calls `_settings()` through its own
# module globals, so the target is `night_shift.bin.is_day_or_night._settings`.
#
# Argument order: the patched mock arrives as the *first* parameter, and the
# fixtures (`mock_settings`) come after it. pytest can tell them apart
# because it knows how many arguments `@patch` supplies.
@patch("night_shift.bin.is_day_or_night._settings")
def test_settings(mock_settings_func, mock_settings):
    mock_settings_func.return_value = mock_settings
    # LEARN: This is a *smoke test*. There's no assert, so it only proves
    # the function runs without raising. Useful, but weak. The tests below
    # check the actual behavior.
    is_day_or_night()


@patch("night_shift.bin.is_day_or_night._settings")
def test_is_day_or_night_during_day(mock_settings_func, mock_settings):
    """Test detection of daytime"""
    # LEARN: A docstring on a test shows up in some reports and IDEs. A
    # descriptive function name does the same job; pytest prints the name.
    mock_settings_func.return_value = mock_settings

    # LEARN: `patch` also works as a context manager. The fake only exists
    # inside the `with` block, which lets one test patch several times.
    #
    # Why mock `datetime`? The code calls `datetime.now()`, so without a mock
    # this test would pass or fail depending on the time of day you run it:
    # a *non-deterministic* test. Faking the clock pins it down. JS does the
    # same with `jest.useFakeTimers().setSystemTime(...)`.
    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        # LEARN: Mocks chain. `datetime.now()` returns a mock, and calling
        # `.strftime()` on *that* returns "12:00". Each `.return_value` is
        # one step down the call chain `now().strftime(...)`.
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night()

        # LEARN: Mocks record how they were called. `assert_called_with`
        # checks the *most recent* call, which is Mockito's `verify(...)` or
        # Jest's `toHaveBeenLastCalledWith(...)`.
        mock_settings.set_string.assert_called_with("day-or-night", "day")

    # LEARN: *Boundary testing.* Bugs cluster at the edges, so the cases
    # below sit right around the thresholds: 05:59 vs 06:00 (sunrise) and
    # 18:29 vs 18:30 (sunset). They prove the code uses `<=` for sunrise and
    # `<` for sunset. Swap an operator in the source and one of these fails.
    #
    # Style note: five cases in one test means the first failure hides the
    # rest. `@pytest.mark.parametrize` (see test_cli.py) would turn each case
    # into its own test. Try refactoring this as an exercise.
    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "05:59"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "06:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:29"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:30"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("night_shift.bin.is_day_or_night._settings")
def test_is_day_or_night_during_night(mock_settings_func, mock_settings):
    """Test detection of nighttime"""
    mock_settings_func.return_value = mock_settings

    with patch("night_shift.bin.is_day_or_night.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


# LEARN: `xfail` means "expected to fail". This test describes the *correct*
# behavior, but the code has a known bug, so it fails today and pytest
# reports it as `x` (xfailed) instead of a red F.
#
#   strict=True     - if the test unexpectedly *passes* (someone fixed the
#                     bug), pytest reports a failure (XPASS strict). That
#                     reminds you to delete this marker, so it can't rot.
#   raises=...      - only count it as the expected failure if it fails with
#                     *this* exception. Any other error is a real failure.
#                     This stops the test "passing as xfail" for the wrong
#                     reason.
#
# The closest JS equivalent is `test.failing(...)`. JUnit has no direct one.
#
# Try it: fix `_settings()` in src/night_shift/bin/is_day_or_night.py, run
# `python3.12 -m pytest tests/test_is_day_or_night.py`, watch it XPASS, then
# delete these five lines.
@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="BUG: _settings() calls _get_schema_source.lookup without calling _get_schema_source()",
)
# LEARN: This patches a whole *module* (`Gio`) rather than one function.
# Every attribute accessed on it (`Gio.Settings.new_full(...)`, ...) becomes
# an auto-created mock. That's how we test GNOME code without GNOME
# installed. See test_settings.py for more.
@patch("night_shift.bin.is_day_or_night.Gio")
def test_settings_builds_gio_settings(mock_gio):
    from night_shift.bin import is_day_or_night as module

    # LEARN: The module caches the schema source in a global. Reset it so
    # this test doesn't depend on whatever an earlier test left behind. Test
    # order must never matter.
    module._schema_source = None
    settings = module._settings()

    # LEARN: `is` checks identity (same object), like `===` on objects in JS.
    # `==` checks equality, like `.equals()` in Java.
    assert settings is mock_gio.Settings.new_full.return_value
