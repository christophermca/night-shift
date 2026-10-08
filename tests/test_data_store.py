import shutil
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from gi.repository import Gio, GLib

import gnome_night_shift
from gnome_night_shift import data_store
from gnome_night_shift.data_store import DataStore
from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from gnome_night_shift.bin.settings import Settings

SCHEMA_XML = next(
    (Path(gnome_night_shift.__file__).parent / "schemas").glob("*.gschema.xml")
)


@pytest.fixture
def store(tmp_path):
    """A DataStore backed by a real Gio.Settings built from the package schema.

    The schema is compiled into tmp_path under the id DataStore looks up, and
    the settings live in GLib's in-memory backend, so nothing touches dconf.
    """
    if shutil.which("glib-compile-schemas") is None:
        pytest.skip("glib-compile-schemas is not installed")

    xml = SCHEMA_XML.read_text()
    real_id = xml.split('schema id="', 1)[1].split('"', 1)[0]
    xml = xml.replace(f'id="{real_id}"', f'id="{data_store.SCHEMA_ID}"')
    (tmp_path / f"{data_store.SCHEMA_ID}.gschema.xml").write_text(xml)
    subprocess.run(["glib-compile-schemas", str(tmp_path)], check=True)

    store = DataStore(str(tmp_path))
    store.data = Gio.Settings.new_full(
        store.schema, Gio.memory_settings_backend_new(), None
    )
    return store


@pytest.mark.parametrize(
    "key, value, expected",
    [
        ("times", GLib.Variant("(ss)", ("06:52", "18:51")), ("06:52", "18:51")),
        (
            "last-known-coordinates",
            GLib.Variant("(dd)", (40.7, -74.0)),
            (40.7, -74.0),
        ),
        ("tzid", "America/New_York", "America/New_York"),
        ("use-geoclue", False, False),  # default is true, so save False
    ],
    ids=["variant-ss", "variant-dd", "string", "bool"],
)
def test_set_saves_each_type(store, key, value, expected):
    store.set(key, value)

    assert store.data[key] == expected


def test_set_rejects_unsupported_types(store):
    with pytest.raises(TypeError, match="can't save times: unsupported type"):
        store.set("times", ["06:52", "18:51"])


@patch("gnome_night_shift.bin.get_sunrise_sunset.requests.get")
def test_fetched_times_are_saved_through_settings(mock_get, store, capsys):
    """The -w path end to end: fetch -> _save -> Settings -> DataStore."""
    response = MagicMock()
    response.json.return_value = {
        "sunrise": "2026-09-25T06:52:10-04:00",
        "sunset": "2026-09-25T18:51:30-04:00",
        "tzid": "America/New_York",
    }
    mock_get.return_value = response
    fetcher = GetTimeOfSunriseSunset(settings=Settings(store))

    fetcher._get_sunrise_sunset(40.7, -74.0, False)

    assert "ERROR SAVING" not in capsys.readouterr().out
    assert store.data["times"] == ("06:52", "18:51")
    assert store.data["tzid"] == "America/New_York"
