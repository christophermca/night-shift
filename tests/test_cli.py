# LEARN: Lesson 3, fixtures in depth, parametrize, and testing a CLI.
#
# `night_shift.main()` is a router: it parses argv and calls the right
# function. Unit-testing a router means checking "flag X calls Y". We don't
# need Y to actually do anything, so Y is mocked every time.
import pytest
from unittest.mock import patch
import night_shift


# LEARN: A fixture can ask for *other* fixtures just by naming them as
# parameters. pytest works out the dependency graph and injects them, the
# way Spring or Dagger inject constructor arguments in Java.
#
# `monkeypatch` is a built-in fixture for temporarily changing things
# (attributes, dict entries, env vars) that are undone automatically when
# the test ends. Here it swaps `sys.argv`, so `argparse` sees whatever
# command line we like.
#
# This is a *factory fixture*: rather than returning a value it returns a
# function, so each test can pick its own arguments:
#     argv("--check-now")  ->  sys.argv = ["night-shift", "--check-now"]
@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["night-shift", *args])

    return set_args


# LEARN: A `yield` fixture handles setup AND teardown in one function:
#     code before `yield` -> beforeEach / @BeforeEach
#     the yielded value   -> what the test receives
#     code after `yield`  -> afterEach / @AfterEach (runs even if the test fails)
# Here the teardown is hidden in the `with` block: when the fixture resumes
# after `yield`, the `with` exits and the patch is undone.
#
# Note the target: `night_shift.GetTimeOfSunriseSunset`, the name as
# `night_shift/__init__.py` imported it, not the class's home module.
@pytest.fixture
def mock_fetcher():
    with patch("night_shift.GetTimeOfSunriseSunset") as fetcher:
        yield fetcher


def test_lat_lng_fetches_for_coords(argv, mock_fetcher):
    # LEARN: The blank lines split every test into Arrange / Act / Assert
    # (also called Given / When / Then). One act per test keeps failures easy
    # to read.
    argv("40.7", "-74.0")
    # LEARN: `mock_fetcher` stands in for the *class*. Calling it
    # (`GetTimeOfSunriseSunset(...)`) gives `mock_fetcher.return_value`, the
    # fake *instance*. `main()` then calls that instance, which gives
    # `.return_value.return_value`. Read it as: class() -> instance() -> result.
    mock_fetcher.return_value.return_value = ("06:52", "18:51")

    assert night_shift.main() == ("06:52", "18:51")
    # LEARN: argparse hands over strings, not floats, and this test records
    # that. Whether it's *desired* behavior is a separate question. Tests
    # often surface questions like this.
    mock_fetcher.return_value.assert_called_once_with(("40.7", "-74.0"), False)


def test_check_now_runs_check(argv):
    argv("--check-now")

    with patch("night_shift.check") as check:
        night_shift.main()

    # LEARN: `assert_called_once_with()` with no arguments means "called
    # once, with no arguments". That's stricter than `assert_called_once()`,
    # which ignores the arguments.
    check.assert_called_once_with()


def test_geoclue_runs_once_with_geoclue(argv, mock_fetcher):
    argv("-g", "-v", "-f")

    night_shift.main()

    # LEARN: The positional args are (verbose, override, use_geoclue). That
    # makes a bare `(True, True, True)` hard to read, and it can't catch
    # two arguments being swapped. Code that uses keyword args tends to be
    # easier to test.
    mock_fetcher.assert_called_once_with(True, True, True)


# LEARN: `@pytest.mark.parametrize` runs one test body with several inputs,
# and each row is reported as its own test:
#     test_systemd_unit_flags[--install-systemd-units-setup]  PASSED
#     test_systemd_unit_flags[--remove-systemd-units-destroy] PASSED
# It's Jest's `test.each` or JUnit 5's `@ParameterizedTest` + `@CsvSource`.
# The first argument is a comma-separated list of parameter names. Each
# tuple in the list is one row.
@pytest.mark.parametrize(
    "flag, method",
    [
        ("--install-systemd-units", "setup"),
        ("--remove-systemd-units", "destroy"),
    ],
)
def test_systemd_unit_flags(argv, flag, method):
    argv(flag)

    with patch("night_shift.Services") as services:
        night_shift.main()

    # LEARN: `getattr(obj, "name")` is Python's `obj["name"]` or
    # `obj[method]` in JS, and it's how the row picks which method to check.
    getattr(services.return_value, method).assert_called_once_with()


def test_no_args_prints_help(argv, mock_fetcher, capsys):
    argv()

    night_shift.main()

    # LEARN: `capsys.readouterr()` returns `(out, err)` and *clears* the
    # buffer, so a second call only sees output printed after the first.
    assert "usage:" in capsys.readouterr().out
    # LEARN: Asserting that something did NOT happen matters just as much.
    # Here it proves "no args" doesn't quietly start a network fetch.
    mock_fetcher.assert_not_called()


def test_run_once_checks_when_asked(mock_fetcher):
    with patch("night_shift.check") as check:
        night_shift.run_once(check_now=True)

    check.assert_called_once_with()


def test_run_once_catches_fetch_errors(mock_fetcher, capsys):
    # LEARN: The mock *class* raises when it's constructed, which simulates
    # `GetTimeOfSunriseSunset(...)` blowing up (no network, say). The test
    # proves `run_once` catches it rather than crashing.
    mock_fetcher.side_effect = RuntimeError("offline")

    night_shift.run_once()

    assert "ERROR during run_once(): offline" in capsys.readouterr().out


def test_run_once_catches_check_errors(mock_fetcher, capsys):
    # LEARN: `patch(...)` takes the same keyword args as MagicMock, so you
    # can set up `side_effect` / `return_value` inline.
    with patch("night_shift.check", side_effect=RuntimeError("no schema")):
        night_shift.run_once(check_now=True)

    assert "check failed: no schema" in capsys.readouterr().out
