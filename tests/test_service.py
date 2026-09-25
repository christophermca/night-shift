import os
import pytest
from unittest.mock import patch, call
from night_shift.lib import service
from night_shift.lib.service import Services

UNITS = ["a.timer", "a.service", "b.timer"]


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    source = tmp_path / "systemd" / "user"
    source.mkdir(parents=True)
    for name in UNITS:
        (source / name).write_text(f"[Unit]\nDescription={name}\n")

    target = tmp_path / "target"
    monkeypatch.setattr(service, "systemd_dir", source)
    monkeypatch.setattr(service, "target_dir", target)
    return source, target


@pytest.fixture
def mock_run():
    with patch("night_shift.lib.service.subprocess.run") as run:
        yield run


def test_init_collects_units_and_timers(dirs):
    services = Services()

    assert sorted(u.name for u in services.all_units) == sorted(UNITS)
    assert sorted(u.name for u in services.timers) == ["a.timer", "b.timer"]


def test_init_refuses_non_linux(dirs, monkeypatch):
    monkeypatch.setattr(service.sys, "platform", "darwin")

    with pytest.raises(SystemExit):
        Services()


def test_symlink_links_every_unit(dirs):
    source, target = dirs

    Services()._symlink()

    for name in UNITS:
        link = target / name
        assert link.is_symlink()
        assert os.readlink(link) == str(source / name)


def test_symlink_replaces_stale_symlink(dirs, tmp_path):
    source, target = dirs
    target.mkdir()
    (target / "a.timer").symlink_to(tmp_path / "old")

    Services()._symlink()

    assert os.readlink(target / "a.timer") == str(source / "a.timer")


def test_symlink_skips_regular_file(dirs, capsys):
    _, target = dirs
    target.mkdir()
    (target / "a.timer").write_text("user's own unit")

    Services()._symlink()

    assert not (target / "a.timer").is_symlink()
    assert (target / "a.timer").read_text() == "user's own unit"
    assert "skipping a.timer :: file exists" in capsys.readouterr().out


def test_setup_links_then_reloads_daemon(dirs, mock_run):
    _, target = dirs

    Services().setup()

    assert (target / "a.timer").is_symlink()
    assert mock_run.call_args_list[0] == call(
        ["systemctl", "--user", "daemon-reload"], check=True
    )


@pytest.mark.xfail(
    strict=True,
    reason="BUG: `systemctl enable` is outside the for loop, so only the last timer is enabled",
)
def test_start_services_enables_every_timer(dirs, mock_run):
    Services()._start_services()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "enable", "--now", timer], check=True
        )


@pytest.mark.xfail(
    strict=True,
    reason="BUG: `systemctl disable` is outside the for loop, so only the last timer is disabled",
)
def test_stop_services_disables_every_timer(dirs, mock_run):
    Services()._stop_services()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "disable", "--now", timer], check=True
        )


def test_start_services_catches_systemctl_failure(dirs, mock_run, capsys):
    import subprocess

    mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")

    Services()._start_services()

    assert "Error:" in capsys.readouterr().out


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="BUG: _remove_symlink iterates self.units, which doesn't exist (should be self.all_units)",
)
def test_destroy_removes_symlinks(dirs, mock_run):
    _, target = dirs
    services = Services()
    services._symlink()

    services.destroy()

    assert list(target.iterdir()) == []
