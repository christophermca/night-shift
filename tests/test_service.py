# `Services` creates symlinks in ~/.local/share/systemd/user and runs
# `systemctl`. Running that for real in a test would change your actual
# machine, so we split it two ways:
#   - filesystem: use a REAL temp directory, since symlinks are cheap and
#                 checking real files is more convincing than mocking `os`
#   - systemctl:  MOCK it, since it has side effects we can't undo or run in CI
# Picking "real where it's cheap and safe, fake where it isn't" is the core
# judgment call in unit testing.
import os
import pytest
from unittest.mock import patch, call
from gnome_night_shift.services import Services

UNITS = ["a.timer", "a.service", "b.timer"]


# tmp_path` is a built-in fixture that gives each test its own
# fresh temp directory as a `pathlib.Path`. pytest creates it and cleans up
# old ones for you.
#
# `tmp_path / "systemd" / "user"` is `path.join(tmp, "systemd", "user")`.
@pytest.fixture
def dirs(tmp_path):
    source = tmp_path / "services" / "systemd" / "user"
    source.mkdir(parents=True)  # like `mkdir -p`
    for name in UNITS:
        (source / name).write_text(f"[Unit]\nDescription={name}\n")

    target = tmp_path / "target"
    return source, target


@pytest.fixture
def mock_run():
    with patch("subprocess.run") as run:
        yield run


def test_init_collects_units_and_timers(dirs):
    source, target = dirs
    services = Services(source, target)

    assert sorted(u.name for u in services.all_units) == sorted(UNITS)
    assert sorted(u.name for u in services.timers) == ["a.timer", "b.timer"]


def test_init_refuses_non_linux(dirs, monkeypatch):
    # mock using macOS
    import sys

    monkeypatch.setattr(sys, "platform", "darwin")

    with pytest.raises(SystemExit):
        Services()


def test_symlink_links_every_unit(dirs):
    source, target = dirs

    Services(source, target)._symlink()

    for name in UNITS:
        link = target / name
        assert link.is_symlink()
        assert os.readlink(link) == str(source / name)


def test_symlink_replaces_stale_symlink(dirs, tmp_path):
    source, target = dirs
    target.mkdir()
    (target / "a.timer").symlink_to(tmp_path / "old")

    Services(source, target)._symlink()

    assert os.readlink(target / "a.timer") == str(source / "a.timer")


def test_symlink_skips_regular_file(dirs, capsys):
    _, target = dirs
    target.mkdir()
    (target / "a.timer").write_text("user's own unit")

    Services(_, target)._symlink()

    assert not (target / "a.timer").is_symlink()
    assert (target / "a.timer").read_text() == "user's own unit"
    assert "skipping a.timer :: file exists" in capsys.readouterr().out


def test_setup_links_then_reloads_daemon(dirs, mock_run):
    _, target = dirs

    Services(_, target).setup()

    assert (target / "a.timer").is_symlink()
    assert mock_run.call_args_list[0] == call(
        ["systemctl", "--user", "daemon-reload"], check=True
    )


def test_start_services_enables_every_timer(dirs, mock_run):
    source, target = dirs
    Services(source, target)._start_services()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "enable", "--now", timer], check=True
        )


def test_stop_services_disables_every_timer(dirs, mock_run):
    source, target = dirs
    Services(source, target)._stop_services()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "disable", "--now", timer], check=True
        )


def test_stop_services_reloads_daemon(dirs, mock_run):
    source, target = dirs
    Services(source, target)._stop_services()

    assert mock_run.call_args_list[0] == call(
        ["systemctl", "--user", "daemon-reload"], check=True
    )


def test_start_services_catches_systemctl_failure(dirs, mock_run, capsys):
    source, target = dirs

    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")

    Services(source, target)._start_services()

    assert "Error:" in capsys.readouterr().out


# Test method: destroy()
def test_destroy_removes_symlinks(dirs, mock_run):
    _, target = dirs
    services = Services(_, target)
    services._symlink()

    services.destroy()

    assert list(target.iterdir()) == []


def test_destroy_keeps_custom_user_unit_files(dirs, mock_run):
    source, target = dirs
    target.mkdir()
    (target / "a.timer").write_text("new custom user unit")

    Services(source, target).destroy()

    assert (target / "a.timer").read_text() == "new custom user unit"


def test_destroy_removes_dangling_symlinks(dirs, mock_run, tmp_path):
    source, target = dirs
    target.mkdir()
    (target / "a.timer").symlink_to(tmp_path / "gone")  # points at nothing

    Services(source, target).destroy()

    assert not (target / "a.timer").is_symlink()


def test_destroy_disables_timers(dirs, mock_run):
    source, target = dirs
    Services(source, target).destroy()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "disable", "--now", timer], check=True
        )
