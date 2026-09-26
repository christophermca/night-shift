import shlex
import tomllib
from pathlib import Path

import pytest
import night_shift
from unittest.mock import patch

UNIT_DIR = Path(night_shift.__file__).parent / "systemd" / "user"
SERVICE_UNITS = sorted(UNIT_DIR.glob("*.service"))
PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["night-shift", *args])

    return set_args


@pytest.fixture
def mock_fetcher():
    with patch("night_shift.GetTimeOfSunriseSunset") as fetcher:
        yield fetcher


def test_lat_lng_fetches_for_coords(argv, mock_fetcher):
    argv("40.7", "-74.0")
    expected_args = (40.7, -74.0)
    mock_fetcher.return_value.return_value = ("06:52", "18:51")

    assert night_shift.main() == ("06:52", "18:51")

    mock_fetcher.return_value.assert_called_once_with(expected_args, False)


def test_lat_lng_fetches_for_coords_and_checks(argv, mock_fetcher):
    argv("40.7", "-74.0", "--check-now")
    expected_args = (40.7, -74.0)
    mock_fetcher.return_value.return_value = ("06:52", "18:51")

    assert night_shift.main() == ("06:52", "18:51")

    mock_fetcher.return_value.assert_called_once_with(expected_args, False)


def test_non_numeric_coordinate_is_a_usage_error(argv, mock_fetcher):
    argv("abc", "-74.0")

    with pytest.raises(SystemExit) as exc:
        night_shift.main()

    assert exc.value.code == 2
    mock_fetcher.assert_not_called()


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


def test_check_runs_is_day_or_night():
    with patch("night_shift.is_day_or_night") as is_day_or_night:
        night_shift.check()
        is_day_or_night.assert_called_once()


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


def _exec_start(unit):
    lines = [
        line.removeprefix("ExecStart=")
        for line in unit.read_text().splitlines()
        if line.startswith("ExecStart=")
    ]
    assert len(lines) == 1, f"{unit.name}: expected exactly one ExecStart line"
    return shlex.split(lines[0])


def test_service_units_are_found():
    # Guards the parametrized test below: an empty glob would make it
    # collect zero cases and pass without checking anything.
    assert SERVICE_UNITS, f"no *.service files in {UNIT_DIR}"


@pytest.mark.parametrize("unit", SERVICE_UNITS, ids=lambda p: p.name)
def test_unit_execstart_is_a_valid_command(unit, argv, mock_fetcher, capsys):
    program, *args = _exec_start(unit)
    scripts = tomllib.loads(PYPROJECT.read_text())["project"]["scripts"]
    argv(*args)

    with patch("night_shift.check"), patch("night_shift.Services"):
        try:
            night_shift.main()
        except SystemExit as exc:  # argparse exits 2 on an unknown flag
            pytest.fail(
                f"{unit.name}: night-shift rejected {args}: "
                f"{capsys.readouterr().err.strip()} (exit {exc.code})"
            )

    assert Path(program).name in scripts
    assert (
        "usage:" not in capsys.readouterr().out
    ), f"{unit.name}: {args} only printed help, so the unit does nothing"
