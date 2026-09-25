from unittest.mock import patch
from night_shift.bin.settings import Settings


@patch("night_shift.bin.settings.Gio")
def test_call_returns_gio_settings(mock_gio):
    settings = Settings()

    assert settings() is mock_gio.Settings.new_full.return_value


@patch("night_shift.bin.settings.Gio")
def test_looks_up_night_shift_schema(mock_gio):
    Settings()

    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    source.lookup.assert_called_once_with(
        "org.gnome.shell.extensions.night-shift", True
    )
    schema_dir = mock_gio.SettingsSchemaSource.new_from_directory.call_args.args[0]
    assert schema_dir.endswith(
        "gnome-shell/extensions/night-shift@christophermca.github.io/schemas"
    )


@patch("night_shift.bin.settings.Gio")
def test_lookup_error_is_caught(mock_gio, capsys):
    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    source.lookup.side_effect = RuntimeError("schema missing")

    settings = Settings()

    assert not hasattr(settings, "settings")
    assert "Error schema missing" in capsys.readouterr().out
