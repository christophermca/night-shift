import shlex
import tomllib
from pathlib import Path

import pytest
import gnome_night_shift
from unittest.mock import patch

UNIT_DIR = (
    Path(gnome_night_shift.__file__).parent / "services" / "systemd" / "user"
)
SERVICE_UNITS = sorted(UNIT_DIR.glob("*.service"))
PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"


@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["gnome_night-shift", *args])

    return set_args


@pytest.fixture
def mock_fetcher():
    with patch("gnome_night_shift.GetTimeOfSunriseSunset") as fetcher:
        yield fetcher


@pytest.fixture(autouse=True)
def settings_class():
    """main() builds one Settings per run; fake it so no test touches GSettings."""
    with patch("gnome_night_shift.Settings") as settings_class:
        yield settings_class


def test_lat_lng_fetches_and_exits_cleanly(argv, mock_fetcher):
    argv("40.7", "-74.0")

    with patch("gnome_night_shift.check") as check:
        result = gnome_night_shift.main()

    mock_fetcher.return_value.assert_called_once_with((40.7, -74.0), False)
    check.assert_not_called()
    assert result is None  # console script does sys.exit(main()): None -> 0


def test_lat_lng_with_check_now_checks_the_fetched_times(
    argv, mock_fetcher, settings_class
):
    argv("40.7", "-74.0", "--check-now")
    mock_fetcher.return_value.return_value = ("06:52", "18:51")

    with patch("gnome_night_shift.check") as check:
        gnome_night_shift.main()

    settings = settings_class.return_value
    settings_class.assert_called_once_with()  # one Settings for the whole run
    mock_fetcher.assert_called_once_with(False, False, settings=settings)
    mock_fetcher.return_value.assert_called_once_with((40.7, -74.0), False)
    check.assert_called_once_with(("06:52", "18:51"), settings)


def test_non_numeric_coordinate_is_a_usage_error(argv, mock_fetcher):
    argv("abc", "-74.0")

    with pytest.raises(SystemExit) as exc:
        gnome_night_shift.main()

    assert exc.value.code == 2
    mock_fetcher.assert_not_called()


def test_check_now_runs_check(argv, settings_class):
    argv("--check-now")

    with patch("gnome_night_shift.check") as check:
        gnome_night_shift.main()

    settings_class.assert_called_once_with()

    check.assert_called_once_with(settings=settings_class.return_value)


def test_geoclue_runs_once_with_geoclue(argv, mock_fetcher, settings_class):
    argv("-g", "-v", "-f")

    gnome_night_shift.main()

    settings_class.assert_called_once_with()

    verbose = True
    override = True
    use_geoclue = True

    mock_fetcher.assert_called_once_with(
        verbose, override, use_geoclue, settings=settings_class.return_value
    )


# `@pytest.mark.parametrize` runs one test body with several inputs,
# and each row is reported as its own test:
#     test_systemd_unit_flags[--install-systemd-units-setup]  PASSED
#     test_systemd_unit_flags[--remove-systemd-units-destroy] PASSED
#
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

    with patch("gnome_night_shift.Services") as services:
        gnome_night_shift.main()

    getattr(services.return_value, method).assert_called_once_with()


def test_no_args_prints_help(argv, mock_fetcher, capsys):
    argv()

    gnome_night_shift.main()

    # `capsys.readouterr()` returns `(out, err)` and *clears* the
    # buffer, so a second call only sees output printed after the first.
    assert "usage:" in capsys.readouterr().out
    # Asserting that something did NOT happen matters just as much.
    # Here it proves "no args" doesn't quietly start a network fetch.
    mock_fetcher.assert_not_called()


def test_check_without_times_uses_saved_times():
    with patch("gnome_night_shift.is_day_or_night") as is_day_or_night:
        gnome_night_shift.check()

    is_day_or_night.assert_called_once_with(None, None)


def test_check_passes_times_through_and_returns_none():
    with patch("gnome_night_shift.is_day_or_night", return_value="day") as fn:
        result = gnome_night_shift.check(("06:52", "18:51"))

    fn.assert_called_once_with(("06:52", "18:51"), None)
    assert result is None  # a string here would become exit status 1


def test_check_passes_settings_through():
    settings = object()

    with patch("gnome_night_shift.is_day_or_night") as fn:
        gnome_night_shift.check(("06:52", "18:51"), settings)

    fn.assert_called_once_with(("06:52", "18:51"), settings)


def test_run_once_checks_the_fetched_times(mock_fetcher):
    mock_fetcher.return_value.times = ("06:52", "18:51")

    with patch("gnome_night_shift.check") as check:
        gnome_night_shift.run_once(check_now=True)

    check.assert_called_once_with(("06:52", "18:51"), None)


def test_run_once_shares_settings_with_fetch_and_check(mock_fetcher):
    settings = object()
    mock_fetcher.return_value.times = ("06:52", "18:51")

    with patch("gnome_night_shift.check") as check:
        gnome_night_shift.run_once(check_now=True, settings=settings)

    assert mock_fetcher.call_args.kwargs["settings"] is settings
    check.assert_called_once_with(("06:52", "18:51"), settings)


@pytest.mark.parametrize(
    "args", [(), ("--install-systemd-units",)], ids=["help", "install-units"]
)
def test_paths_without_settings_dont_create_them(
    argv, mock_fetcher, settings_class, args
):
    argv(*args)

    with patch("gnome_night_shift.Services"):
        gnome_night_shift.main()

    settings_class.assert_not_called()  # no spurious "settings unavailable"


def test_run_once_catches_fetch_errors(mock_fetcher, capsys):
    # The mock *class* raises when it's constructed, which simulates
    # `GetTimeOfSunriseSunset(...)` blowing up (no network, say). The test
    # proves `run_once` catches it rather than crashing.
    mock_fetcher.side_effect = RuntimeError("offline")

    gnome_night_shift.run_once()

    assert "ERROR during run_once(): offline" in capsys.readouterr().out


def test_run_once_catches_check_errors(mock_fetcher, capsys):
    # `patch(...)` takes the same keyword args as MagicMock, so you
    # can set up `side_effect` / `return_value` inline.
    with patch(
        "gnome_night_shift.check", side_effect=RuntimeError("no schema")
    ):
        gnome_night_shift.run_once(check_now=True)

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

    with patch("gnome_night_shift.check"), patch("gnome_night_shift.Services"):
        try:
            gnome_night_shift.main()
        except SystemExit as exc:  # argparse exits 2 on an unknown flag
            pytest.fail(
                f"{unit.name}: gnome_night-shift rejected {args}: "
                f"{capsys.readouterr().err.strip()} (exit {exc.code})"
            )

    assert Path(program).name in scripts
    assert (
        "usage:" not in capsys.readouterr().out
    ), f"{unit.name}: {args} only printed help, so the unit does nothing"
