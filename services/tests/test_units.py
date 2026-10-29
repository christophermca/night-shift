"""The plugin's systemd units must call the core CLI with flags it accepts."""

import shlex
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10: the same parser, as a package
    import tomli as tomllib

import pytest

import night_shift_services
from night_shift import cli
from night_shift_services import Services

UNIT_DIR = Path(night_shift_services.__file__).parent / "systemd" / "user"
SERVICE_UNITS = sorted(UNIT_DIR.glob("*.service"))
CORE_PYPROJECT = Path(__file__).parents[2] / "pyproject.toml"
TIMES = ("06:52", "18:51")


def _exec_start(unit):
    lines = [
        line.removeprefix("ExecStart=")
        for line in unit.read_text().splitlines()
        if line.startswith("ExecStart=")
    ]
    assert len(lines) == 1, f"{unit.name}: expected exactly one ExecStart line"
    return shlex.split(lines[0])


def test_service_units_are_found():
    # Guards the parametrized tests below: an empty glob would make them
    # collect zero cases and pass without checking anything.
    assert SERVICE_UNITS, f"no *.service files in {UNIT_DIR}"


@pytest.mark.parametrize("unit", SERVICE_UNITS, ids=lambda p: p.name)
def test_unit_execstart_is_a_valid_command(
    unit, argv, mock_fetcher, mock_check, capsys
):
    program, *args = _exec_start(unit)
    scripts = tomllib.loads(CORE_PYPROJECT.read_text())["project"]["scripts"]
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


@pytest.mark.parametrize("unit", SERVICE_UNITS, ids=lambda p: p.name)
def test_setup_with_schema_keeps_what_each_unit_does(
    unit, tmp_path, argv, mock_fetcher, mock_check
):
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
