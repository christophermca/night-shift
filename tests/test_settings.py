# LEARN: Lesson 2, mocking a whole library and reading back how it was called.
#
# `Settings` wraps GNOME's GSettings (`Gio`). Using the real thing needs a
# compiled schema installed in your home directory, which is slow, fragile
# and not something CI has. So we replace the `Gio` module with a mock and
# check that our code *talks to it correctly*. This is the usual approach for
# anything at the edge of your code: network, OS, UI toolkit.
from unittest.mock import patch
from night_shift.bin.settings import Settings


# LEARN: Patch `night_shift.bin.settings.Gio`, the name as *settings.py*
# sees it after `from gi.repository import Gio`. Patching
# `gi.repository.Gio` would be too late, because settings.py already holds
# its own reference to the real module. (Same "patch where it's looked up"
# rule as in lesson 1.)
@patch("night_shift.bin.settings.Gio")
def test_call_returns_gio_settings(mock_gio):
    settings = Settings()

    # LEARN: We never told the mock what `new_full` returns, but MagicMock
    # auto-creates a `return_value` and always hands back the *same* one.
    # So "the thing new_full returned" is something we can compare against,
    # with no setup needed.
    assert settings() is mock_gio.Settings.new_full.return_value


@patch("night_shift.bin.settings.Gio")
def test_looks_up_night_shift_schema(mock_gio):
    Settings()

    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    # LEARN: `assert_called_once_with` checks two things: called exactly
    # once, AND with exactly these arguments. It's Mockito's
    # `verify(mock, times(1)).lookup(...)`.
    source.lookup.assert_called_once_with(
        "org.gnome.shell.extensions.night-shift", True
    )
    # LEARN: When you only care about *one* argument, read it back out of
    # the mock instead of asserting the whole call. `call_args` is the most
    # recent call: `.args` is the tuple of positional args and `.kwargs` is
    # the dict of keyword args. This is Mockito's `ArgumentCaptor`, or
    # `mock.calls[0][0]` in Jest.
    schema_dir = mock_gio.SettingsSchemaSource.new_from_directory.call_args.args[0]
    assert schema_dir.endswith(
        "gnome-shell/extensions/night-shift@christophermca.github.io/schemas"
    )


# LEARN: `capsys` is a built-in pytest fixture that captures everything
# printed to stdout/stderr during the test. Name it as a parameter and it's
# yours, with no import needed. See test_cli.py for more on fixtures.
@patch("night_shift.bin.settings.Gio")
def test_lookup_error_is_caught(mock_gio, capsys):
    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    # LEARN: `side_effect` set to an exception makes the mock *raise* when
    # called. This is Mockito's `thenThrow(...)`, or Jest's
    # `mockImplementation(() => { throw ... })`. It's how you test error
    # paths without breaking anything real.
    source.lookup.side_effect = RuntimeError("schema missing")

    settings = Settings()

    # LEARN: Test what the code *actually* does, even when it's odd. On
    # error `__init__` prints and never sets `self.settings`. Pinning that
    # down means you'll notice if it changes, whether you meant it to or not.
    assert not hasattr(settings, "settings")
    assert "Error schema missing" in capsys.readouterr().out
