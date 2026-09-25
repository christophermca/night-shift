import pytest
from unittest.mock import patch
import night_shift


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
    mock_fetcher.return_value.return_value = ("06:52", "18:51")

    assert night_shift.main() == ("06:52", "18:51")
    mock_fetcher.return_value.assert_called_once_with(("40.7", "-74.0"), False)


def test_check_now_runs_check(argv):
    argv("--check-now")

    with patch("night_shift.check") as check:
        night_shift.main()

    check.assert_called_once_with()


def test_geoclue_runs_once_with_geoclue(argv, mock_fetcher):
    argv("-g", "-v", "-f")

    night_shift.main()

    mock_fetcher.assert_called_once_with(True, True, True)


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

    getattr(services.return_value, method).assert_called_once_with()


def test_no_args_prints_help(argv, mock_fetcher, capsys):
    argv()

    night_shift.main()

    assert "usage:" in capsys.readouterr().out
    mock_fetcher.assert_not_called()


def test_run_once_checks_when_asked(mock_fetcher):
    with patch("night_shift.check") as check:
        night_shift.run_once(check_now=True)

    check.assert_called_once_with()


def test_run_once_catches_fetch_errors(mock_fetcher, capsys):
    mock_fetcher.side_effect = RuntimeError("offline")

    night_shift.run_once()

    assert "ERROR during run_once(): offline" in capsys.readouterr().out


def test_run_once_catches_check_errors(mock_fetcher, capsys):
    with patch("night_shift.check", side_effect=RuntimeError("no schema")):
        night_shift.run_once(check_now=True)

    assert "check failed: no schema" in capsys.readouterr().out
