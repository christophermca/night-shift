import os
from pathlib import Path
from gi.repository import Gio


class Settings:
    def __call__(self, *args, **kwargs):
        return self.settings

    def __init__(self):
        # Load schema
        SCHEMA_ID = "org.gnome.shell.extensions.night-shift"

        schema_dir = os.path.expanduser(
            Path.home()
            / ".local"
            / "share"
            / "gnome-shell"
            / "extensions"
            / "night-shift@christophermca.github.io"
            / "schemas"
        )

        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_dir, Gio.SettingsSchemaSource.get_default(), False
        )

        try:
            # initialize gsettings obj
            schemaObj = schema_source.lookup(SCHEMA_ID, True)
            settings = Gio.Settings.new_full(schemaObj, None, None)

            self.settings = settings

        except Exception as e:
            print(f"Error {e}")
            return None


if __name__ == "__main__":
    main()
