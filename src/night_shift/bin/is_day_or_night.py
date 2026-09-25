#!/usr/bin/python

import os
import gi

from datetime import datetime
from pathlib import Path

gi.require_version("Gio", "2.0")
from gi.repository import Gio, GLib

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

# Schema is loaded lazily (on first use) rather than at import time, so this
# module can be imported/tested without a compiled schema on disk.
_schema_source = None


def _get_schema_source():
    global _schema_source
    if _schema_source is None:
        _schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_dir, Gio.SettingsSchemaSource.get_default(), False
        )
    return _schema_source


def is_day_or_night():
    settings = _settings()

    times: list[str] = settings.get_value("times")
    print(f"times{times}")
    [sunrise, sunset] = times
    current_time = datetime.now().strftime("%H:%M")  # 24hr format

    # check if currrent time is after sunrise or sunset
    DAY_NIGHT: str

    if sunrise <= current_time < sunset:
        DAY_NIGHT = "day"
    else:
        DAY_NIGHT = "night"

    # set day-or-night
    if DAY_NIGHT:
        settings.set_string("day-or-night", DAY_NIGHT)

        print(f"{DAY_NIGHT}time")


def _settings() -> object:
    # initialize gsettings obj
    schema_obj = _get_schema_source.lookup(SCHEMA_ID, True)
    settings = Gio.Settings.new_full(schema_obj, None, None)

    return settings


# if __name__ == "__main__":
#     is_day_or_night()
