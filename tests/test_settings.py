from unittest.mock import patch
from gnome_night_shift.bin.settings import Settings


@patch("gnome_night_shift.bin.settings.Gio")
def test_call_returns_gio_settings(mock_gio):
    settings = Settings()

    assert settings() is mock_gio.Settings.new_full.return_value


@patch("gnome_night_shift.bin.settings.Gio")
def test_looks_up_night_shift_schema(mock_gio):
    Settings()

    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    source.lookup.assert_called_once_with(
        "org.gnome.shell.extensions.night-shift", True
    )
    schema_dir = (
        mock_gio.SettingsSchemaSource.new_from_directory.call_args.args[0]
    )
    assert schema_dir.endswith(
        "gnome-shell/extensions/night-shift@christophermca.github.io/schemas"
    )


def test_missing_schema_means_no_settings(tmp_path, monkeypatch, capsys):
    # Real Gio, nothing mocked: an empty HOME is exactly a machine without
    # the GNOME extension installed.
    monkeypatch.setenv("HOME", str(tmp_path))

    settings = Settings()

    assert settings() is None
    assert settings.available is False
    assert "settings unavailable" in capsys.readouterr().err


@patch("gnome_night_shift.bin.settings.Gio")
def test_schema_not_in_directory_means_no_settings(mock_gio, capsys):
    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    source.lookup.return_value = None  # directory exists, schema isn't in it

    settings = Settings()

    assert settings() is None
    mock_gio.Settings.new_full.assert_not_called()
    assert "org.gnome.shell.extensions.night-shift not found" in (
        capsys.readouterr().err
    )


@patch("gnome_night_shift.bin.settings.Gio")
def test_lookup_error_means_no_settings(mock_gio, capsys):
    source = mock_gio.SettingsSchemaSource.new_from_directory.return_value
    source.lookup.side_effect = RuntimeError("schema missing")

    settings = Settings()

    assert settings() is None
    assert "schema missing" in capsys.readouterr().err
