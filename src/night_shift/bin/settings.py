import os
import sys
from pathlib import Path
from gi.repository import Gio

SCHEMA_ID = "org.gnome.shell.extensions.night-shift"


class Settings:
    """Wraps the extension's Gio.Settings.

    `Settings()()` returns the Gio.Settings object, or None when the schema
    isn't installed (for example the GNOME extension is missing). Callers
    must handle None; night-shift keeps working, it just can't save.
    """

    def __call__(self, *args, **kwargs):
        return self.settings

    def __init__(self):
        self.settings = None

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

            self.settings = Gio.Settings.new_full(schema, None, None)

        except Exception as e:
            print(
                f"night-shift: settings unavailable, nothing will be saved ({e})",
                file=sys.stderr,
            )

    @property
    def available(self) -> bool:
        return self.settings is not None
