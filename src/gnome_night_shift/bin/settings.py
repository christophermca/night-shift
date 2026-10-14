import os
from pathlib import Path
from gi.repository import Gio
from gnome_night_shift.data_store import DataStore

SCHEMA_ID = "org.gnome.shell.extensions.night-shift"
DEFAULT_SCHEMA_PATH = os.path.expanduser(
    Path.home()
    / ".local"
    / "share"
    / "gnome-shell"
    / "extensions"
    / "night-shift@christophermca.github.io"
    / "schemas"
)


class Settings:
    """Wraps the extension's Gio.Settings.

    `Settings()` returns the Gio.Settings object, or None when the schema
    isn't installed (for example the GNOME extension is missing). Callers
    must handle None; night-shift keeps working, it just can't save.
    """

    def __init__(self, data_store: DataStore | None = None):

        self.data_store = (
            data_store
            if data_store is not None
            else DataStore(DEFAULT_SCHEMA_PATH)
        )

    @property
    def data(self):
        print(self.data_store.keys())
        return self.data_store.data

    @property
    def available(self) -> bool:
        return self.data_store.available

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
