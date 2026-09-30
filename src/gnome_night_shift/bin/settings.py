import os
import sys
from pathlib import Path
from gi.repository import Gio
from gnome_night_shift.data_store import DataStore

SCHEMA_ID = "org.gnome.shell.extensions.night-shift"


class Settings:
    """Wraps the extension's Gio.Settings.

    `Settings()()` returns the Gio.Settings object, or None when the schema
    isn't installed (for example the GNOME extension is missing). Callers
    must handle None; night-shift keeps working, it just can't save.
    """

    def __init__(self, data_store: DataStore | None = None):

        if data_store is None:
            schema_dir = os.path.expanduser(
                Path.home()
                / ".local"
                / "share"
                / "gnome-shell"
                / "extensions"
                / "night-shift@christophermca.github.io"
                / "schemas"
            )

            try:
                schema_source = Gio.SettingsSchemaSource.new_from_directory(
                    schema_dir, Gio.SettingsSchemaSource.get_default(), False
                )
                schema = schema_source.lookup(SCHEMA_ID, True)
                if schema is None:
                    raise LookupError(f"schema {SCHEMA_ID} not found")

                self.settings = self.use_schema(schema)

            except Exception as e:
                print(
                    f"night-shift: settings unavailable, nothing will be saved ({e})",
                    file=sys.stderr,
                )
        else:
            if data_store.schema:
                self.use_schema(data_store.schema)
                self.data_store = data_store

    def use_schema(self, schema):
        settings = Gio.Settings.new_full(schema, None, None)
        return settings

    @property
    def data(self):
        return self.data_store

    @property
    def available(self) -> bool:
        return self.settings is not None

    def get_keys(self):
        print("START: gettings all keys\n\n")
        try:
            for key, value in self.data_store:
                print(key, value)
        except Exception as e:
            print(f"SOMETHING BAD::: {e}")
        finally:
            print("END: gettings all keys\n")

    def get(self, key: str):
        try:
            return self.data_store.get(key)
        except AttributeError as e:
            print(f"Error: Failed to GET key:`{key}`\nMessage:: {e}")

    def set(self, key, value):
        self.data_store.set(key, value)
