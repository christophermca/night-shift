# LEARN: Lesson 4, testing code that changes the filesystem and runs commands.
#
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
from night_shift.lib import service
from night_shift.lib.service import Services

UNITS = ["a.timer", "a.service", "b.timer"]


# LEARN: `tmp_path` is a built-in fixture that gives each test its own
# fresh temp directory as a `pathlib.Path`. pytest creates it and cleans up
# old ones for you. The nearest equivalent is JUnit 5's `@TempDir`.
#
# `pathlib` note: the `/` operator joins paths, so
# `tmp_path / "systemd" / "user"` is `path.join(tmp, "systemd", "user")`.
@pytest.fixture
def dirs(tmp_path, monkeypatch):
    source = tmp_path / "systemd" / "user"
    source.mkdir(parents=True)  # like `mkdir -p`
    for name in UNITS:
        (source / name).write_text(f"[Unit]\nDescription={name}\n")

    target = tmp_path / "target"
    # LEARN: service.py works out `systemd_dir` and `target_dir` as module
    # *globals* at import time, so there's no argument to pass them in
    # through. `monkeypatch.setattr(module, "name", value)` swaps a global
    # for this one test and restores it afterwards.
    #
    # Design lesson: if these were constructor arguments with defaults,
    # e.g. `Services(target_dir=...)`, the test wouldn't need monkeypatch at
    # all. Code that's hard to test often means hidden dependencies.
    monkeypatch.setattr(service, "systemd_dir", source)
    monkeypatch.setattr(service, "target_dir", target)
    # LEARN: A fixture can return several values as a tuple. Tests unpack
    # it with `source, target = dirs`.
    return source, target


@pytest.fixture
def mock_run():
    with patch("night_shift.lib.service.subprocess.run") as run:
        yield run


def test_init_collects_units_and_timers(dirs):
    services = Services()

    # LEARN: `os.scandir` returns files in no guaranteed order. Sorting both
    # sides first stops this test from failing at random on a different
    # filesystem. Watch out for ordering assumptions: they're a classic
    # source of flaky tests.
    assert sorted(u.name for u in services.all_units) == sorted(UNITS)
    assert sorted(u.name for u in services.timers) == ["a.timer", "b.timer"]


def test_init_refuses_non_linux(dirs, monkeypatch):
    # LEARN: Pretend to be on macOS. monkeypatch works on any object's
    # attributes, including the stdlib `sys` module.
    monkeypatch.setattr(service.sys, "platform", "darwin")

    # LEARN: `pytest.raises` asserts that the block raises this exception
    # type, and the test fails if it doesn't. It's JUnit's
    # `assertThrows(...)` or Jest's `expect(() => ...).toThrow()`.
    # `sys.exit()` raises `SystemExit`, so that's how you test "the program
    # exits" without actually exiting pytest.
    with pytest.raises(SystemExit):
        Services()


def test_symlink_links_every_unit(dirs):
    source, target = dirs

    Services()._symlink()

    # LEARN: `_symlink()` returns nothing. The only way to know it worked is
    # to check its *side effects* on the real (temp) filesystem. Where
    # there's nothing to return, assert on what changed.
    for name in UNITS:
        link = target / name
        assert link.is_symlink()
        assert os.readlink(link) == str(source / name)


def test_symlink_replaces_stale_symlink(dirs, tmp_path):
    source, target = dirs
    target.mkdir()
    # LEARN: The Arrange step builds the exact starting state this branch
    # needs: an old symlink already sitting there. Each `if`/`except` in the
    # source usually earns its own test, which is how you reach the branches
    # that coverage reports as missed.
    (target / "a.timer").symlink_to(tmp_path / "old")

    Services()._symlink()

    assert os.readlink(target / "a.timer") == str(source / "a.timer")


def test_symlink_skips_regular_file(dirs, capsys):
    _, target = dirs  # LEARN: `_` means "I don't need this value"
    target.mkdir()
    (target / "a.timer").write_text("user's own unit")

    Services()._symlink()

    # LEARN: This is a *safety* test: the code must never overwrite a real
    # file the user made. Tests like this guard the behavior that would
    # hurt most if it broke.
    assert not (target / "a.timer").is_symlink()
    assert (target / "a.timer").read_text() == "user's own unit"
    assert "skipping a.timer :: file exists" in capsys.readouterr().out


def test_setup_links_then_reloads_daemon(dirs, mock_run):
    _, target = dirs

    Services().setup()

    assert (target / "a.timer").is_symlink()
    # LEARN: `call_args_list` is every call in order, as a list of `call`
    # objects. You build the expected one with `call(...)`, using the same
    # arguments as the real call, and compare with `==`. Indexing `[0]`
    # checks *order*: systemd must be reloaded before anything is enabled.
    # This is Jest's `mock.calls[0]` or Mockito's `InOrder`.
    assert mock_run.call_args_list[0] == call(
        ["systemctl", "--user", "daemon-reload"], check=True
    )


# LEARN: Two xfail tests for one indentation bug. In `_start_services`,
# `subprocess.run([... "enable" ...])` sits *after* the `for` loop rather
# than inside it, so only the last timer is enabled. The test says what
# SHOULD happen: every timer gets enabled. (xfail is explained in
# test_is_day_or_night.py.)
def test_start_services_enables_every_timer(dirs, mock_run):
    Services()._start_services()

    # LEARN: `assert_any_call` passes if *any* recorded call matches, in any
    # order. It's the right tool when a mock is called several times and
    # the order doesn't matter.
    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "enable", "--now", timer], check=True
        )


def test_stop_services_disables_every_timer(dirs, mock_run):
    Services()._stop_services()

    for timer in ["a.timer", "b.timer"]:
        mock_run.assert_any_call(
            ["systemctl", "--user", "disable", "--now", timer], check=True
        )


def test_start_services_catches_systemctl_failure(dirs, mock_run, capsys):
    import subprocess

    # LEARN: Pretend systemctl exited with status 1. `check=True` in the
    # source makes the real `subprocess.run` raise `CalledProcessError` on
    # a non-zero exit, and the mock copies that by raising it directly.
    mock_run.side_effect = subprocess.CalledProcessError(1, "systemctl")

    Services()._start_services()

    assert "Error:" in capsys.readouterr().out


# LEARN: `raises=AttributeError` makes sure this counts as "expected to
# fail" only because of the known typo (`self.units`). If it ever fails in
# some other way, that shows up as a real failure.
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
