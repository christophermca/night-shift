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

# Load schema
schema_source = Gio.SettingsSchemaSource.new_from_directory(
    schema_dir, Gio.SettingsSchemaSource.get_default(), False
)


def is_day_or_night():
    settings = _settings()

    times: list[str] = settings.get_value("times")
    [sunrise, sunset] = times
    current_time = datetime.now().strftime("%H:%M")  # 24hr format

    # check if currrent time is after sunrise or sunset
    DAY_NIGHT: str

    if current_time >= sunrise:
        DAY_NIGHT = "day"

    if current_time >= sunset:
        DAY_NIGHT = "night"

    # set day-or-night
    if DAY_NIGHT:
        settings.set_string("day-or-night", DAY_NIGHT)


def _settings() -> object:
    # initialize gsettings obj
    schemaObj = schema_source.lookup(SCHEMA_ID, True)
    settings = Gio.Settings.new_full(schemaObj, None, None)

    return settings


if __name__ == "__main__":
    is_day_or_night()
