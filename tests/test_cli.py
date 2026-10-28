import shlex
import tomllib
from pathlib import Path

import pytest
from unittest.mock import ANY, patch

import night_shift
from night_shift import cli

UNIT_DIR = Path(night_shift.__file__).parent / "services" / "systemd" / "user"
SERVICE_UNITS = sorted(UNIT_DIR.glob("*.service"))
PYPROJECT = Path(__file__).parents[1] / "pyproject.toml"
TIMES = ("06:52", "18:51")


@pytest.fixture
def argv(monkeypatch):
    def set_args(*args):
        monkeypatch.setattr("sys.argv", ["night-shift", *args])

    return set_args


@pytest.fixture
def mock_fetcher():
    with patch(
        "night_shift.cli.GetTimeOfSunriseSunset", autospec=True
    ) as fetcher:
        yield fetcher


@pytest.fixture
def mock_check():
    with patch("night_shift.cli.check") as check:
        yield check


@pytest.fixture(autouse=True)
def settings_class():
    """main() builds one Settings per run; fake it so no test touches GSettings."""
    with patch("night_shift.cli.Settings") as settings_class:
        yield settings_class


@pytest.fixture(autouse=True)
def data_store_class():
    """-w / -c SCHEMA_PATH build a DataStore; fake it so no schema is compiled."""
    with patch("night_shift.cli.DataStore") as data_store_class:
        yield data_store_class


@pytest.fixture
def services_class():
    with patch("night_shift.cli.NightShiftServices") as services_class:
        yield services_class


# --- latitude / longitude ---------------------------------------------------


def test_lat_lng_fetches_and_exits_cleanly(
    argv, mock_fetcher, mock_check, settings_class
):
    argv("--lat=40.7", "--lng=-74.0")

    result = cli.main()

    mock_fetcher.assert_called_once_with(
        0, False, settings=settings_class.return_value
    )
    mock_fetcher.return_value.assert_called_with((40.7, -74.0), 0)
    mock_check.assert_not_called()
    assert result is None


def test_lat_lng_with_check_now_flag_checks_the_fetched_times(
    argv, mock_fetcher, mock_check, settings_class
):
    argv("--lat=40.7", "--lng=-74.0", "--check-now")
    mock_fetcher.return_value.return_value = TIMES

    cli.main()

    mock_fetcher.assert_called_once_with(
        0, False, settings=settings_class.return_value
    )
    mock_fetcher.return_value.assert_called_with((40.7, -74.0), 0)

    settings = settings_class.return_value

    settings_class.assert_called_once_with()  # one Settings for the whole run
    mock_check.assert_called_once_with(TIMES, settings, 0)


def test_non_numeric_coordinate_is_a_usage_error(argv, mock_fetcher, capsys):
    argv("--lat=abc", "--lng=-74.0")

    with pytest.raises(SystemExit) as exc:
        cli.main()

    assert exc.value.code == 2
    assert "invalid float value" in capsys.readouterr().err
    mock_fetcher.assert_not_called()


# --- -c / --check-now [SCHEMA_PATH] -------------------------------------------
def test_given_check_now_fails_throws_error(argv, settings_class, capsys):
    argv("--check-now")
    with patch(
        "night_shift.cli.is_day_or_night",
    ) as fn:

        fn.side_effect = AttributeError()
        result = cli.main()

        assert result is None


def test_check_now_uses_default_settings(argv, mock_check, settings_class):
    argv("--check-now")

    result = cli.main()

    mock_check.assert_called_once_with(
        settings=settings_class.return_value, verbose=0
    )
    assert result is None


def test_check_now_with_schema_path_uses_that_data_store(
    argv, mock_check, settings_class, data_store_class
):
    argv("--check-now", "/path/to/schemas")

    cli.main()

    data_store_class.assert_called_once_with("/path/to/schemas")
    settings_class.assert_called_once_with(data_store_class.return_value)
    mock_check.assert_called_once_with(
        settings=settings_class.return_value, verbose=0
    )


# --- -g / --geoclue -----------------------------------------------------------


def test_geoclue_fetches_with_one_shared_settings(
    argv, mock_fetcher, mock_check, settings_class
):
    argv("-g", "-v", "-f")

    cli.main()

    settings_class.assert_called_once_with()
    verbose = 1  # verbose is a count now
    mock_fetcher.assert_called_once_with(
        verbose,
        True,
        True,
        settings_class.return_value,
    )


def test_geoclue_without_check_now_does_not_check(
    argv, mock_fetcher, mock_check
):
    argv("-g")

    cli.main()

    mock_check.assert_not_called()


def test_geoclue_with_check_now_FLAG_checks_the_fetched_times(
    argv, mock_fetcher, mock_check, settings_class
):
    argv("-g", "--check-now")
    mock_fetcher.return_value.times = TIMES

    cli.main()

    mock_check.assert_called_once_with(TIMES, settings_class.return_value, 0)


# --- -w / --watch [SCHEMA_PATH] -----------------------------------------------


def test_watch_with_schema_path_fetches_with_that_data_store(
    argv, mock_fetcher, mock_check, settings_class, data_store_class
):
    argv("--watch", "/path/to/schemas")

    cli.main()

    data_store_class.assert_called_once_with("/path/to/schemas")
    settings_class.assert_called_once_with(data_store_class.return_value)
    mock_fetcher.assert_called_once_with(
        0, False, None, settings_class.return_value
    )


# --- services subcommands -------------------------------------------------------


def test_services_setup_builds_units_for_the_schema(argv, services_class):
    argv("services", "setup", "/path/to/schemas", "--build-only")

    cli.main()

    services_class.assert_called_once_with()
    services_class.return_value.setup.assert_called_once_with(
        "/path/to/schemas", True
    )


@pytest.mark.parametrize(
    "subcommand, method",
    [("start", "start"), ("stop", "stop"), ("taredown", "destroy")],
)
def test_services_subcommands(argv, services_class, subcommand, method):
    argv("services", subcommand)

    cli.main()

    getattr(services_class.return_value, method).assert_called_once_with()


@pytest.mark.parametrize(
    "args",
    [(), ("services", "setup", "/path/to/schemas")],
    ids=["help", "services-setup"],
)
def test_paths_without_settings_dont_create_them(
    argv, services_class, settings_class, args
):
    argv(*args)

    cli.main()

    settings_class.assert_not_called()  # no spurious "settings unavailable"


def test_no_args_prints_help(argv, mock_fetcher, capsys):
    argv()

    cli.main()

    assert "usage:" in capsys.readouterr().out
    mock_fetcher.assert_not_called()


# --- check() and run_once() ------------------------------------------------------


def test_check_passes_times_and_settings_through_and_returns_none():
    settings = object()

    with patch("night_shift.cli.is_day_or_night", autospec=True) as fn:
        result = cli.check(TIMES, settings)

    fn.assert_called_once_with(TIMES, settings, 0)
    assert result is None  # a string here would become exit status 1


def test_check_without_times_uses_saved_times():
    with patch("night_shift.cli.is_day_or_night", autospec=True) as fn:
        cli.check()

    fn.assert_called_once_with(None, None, 0)


def test_run_once_shares_settings_with_fetch_and_check(
    mock_fetcher, mock_check
):
    settings = object()
    mock_fetcher.return_value.times = TIMES

    cli.run_once(check_now=None, settings=settings)  # None: -c given, no path

    mock_fetcher.assert_called_once_with(False, False, False, settings)
    mock_check.assert_called_once_with(TIMES, settings, 0)


def test_run_once_without_check_now_does_not_check(mock_fetcher, mock_check):
    cli.run_once(check_now=False)

    mock_check.assert_not_called()


def test_run_once_catches_fetch_errors(mock_fetcher, capsys):
    mock_fetcher.side_effect = RuntimeError("offline")

    cli.run_once()

    assert "ERROR during run_once(): offline" in capsys.readouterr().out


def test_run_once_catches_check_errors(mock_fetcher, capsys):
    mock_fetcher.return_value.times = ("06:52", "18:51")

    with patch(
        "night_shift.cli.check", side_effect=AttributeError("no schema")
    ) as check:
        cli.run_once(check_now=None)

    check.assert_called_once()

    assert "check failed: no schema" in capsys.readouterr().out


# --- systemd units ---------------------------------------------------------------


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
def test_unit_execstart_is_a_valid_command(
    unit, argv, mock_fetcher, mock_check, services_class, capsys
):
    program, *args = _exec_start(unit)
    scripts = tomllib.loads(PYPROJECT.read_text())["project"]["scripts"]
    argv(*args)

    try:
        cli.main()
    except SystemExit as exc:  # argparse exits 2 on an unknown flag
        pytest.fail(
            f"{unit.name}: night-shift rejected {args}: "
            f"{capsys.readouterr().err.strip()} (exit {exc.code})"
        )

    assert Path(program).name in scripts
    assert (
        "usage:" not in capsys.readouterr().out
    ), f"{unit.name}: {args} only printed help, so the unit does nothing"


@pytest.mark.parametrize(
    "args",
    [
        ["--check-now"],
        ["--check-now", "/path/to/schemas"],
        ["--lat=40.7", "--lng=-74.0", "--check-now"],
        ["-g", "--check-now"],
    ],
    ids=["-c", "-c PATH", "--lat --lng -c", "-g -c"],
)
def test_verbose_reaches_is_day_or_night(argv, mock_fetcher, args):
    argv(*args, "-vv")
    mock_fetcher.return_value.return_value = TIMES  # sunrise_sunset(coords)
    mock_fetcher.return_value.times = TIMES  # run_once reads .times

    with patch("night_shift.cli.is_day_or_night", autospec=True) as fn:
        cli.main()

    # autospec matches by signature, so this passes however check() spells the call
    fn.assert_called_once_with(ANY, ANY, verbose=2)


@pytest.mark.parametrize(
    "args, checks",
    [
        (["--watch", "/path/to/schemas"], False),
        (["--watch", "/path/to/schemas", "--check-now"], False),
    ],
    ids=["-w", "-w -c"],
)
def test_watch_DOESNOT_check_with_check_now(
    argv, mock_fetcher, mock_check, args, checks
):
    argv(*args)
    mock_fetcher.return_value.times = TIMES  # what a real fetch sets

    cli.main()

    assert mock_check.called is checks


@pytest.mark.parametrize("unit", SERVICE_UNITS, ids=lambda p: p.name)
def test_setup_with_schema_keeps_what_each_unit_does(
    unit, tmp_path, argv, mock_fetcher, mock_check
):
    from night_shift.services import Services

    mock_fetcher.return_value.times = TIMES

    def runs_check(text):
        exec_start = next(
            l for l in text.splitlines() if l.startswith("ExecStart=")
        )
        argv(*shlex.split(exec_start.split("=", 1)[1])[1:])
        mock_check.reset_mock()
        cli.main()
        return mock_check.called

    Services(UNIT_DIR, tmp_path)._make_copy_of_unit(
        [unit], "/x/schemas", tmp_path
    )

    assert runs_check((tmp_path / unit.name).read_text()) == runs_check(
        unit.read_text()
    )


def test_watch_without_path_uses_the_default_settings(
    argv, mock_fetcher, settings_class, data_store_class
):
    argv("--watch")

    cli.main()

    settings_class.assert_called_once_with()  # Settings() -> DEFAULT_SCHEMA_PATH
    data_store_class.assert_not_called()
