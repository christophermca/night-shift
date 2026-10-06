#!/usr/bin/python

import sys

from gnome_night_shift.bin.settings import Settings
from datetime import datetime


def is_day_or_night(times=None, settings=None):
    """Work out "day" or "night" and save it.

    `times` is a (sunrise, sunset) pair of "HH:MM" strings. When it's not
    given, the times saved in settings are used.

    `settings` is a `Settings`. When it's not given, raise an Error to the caller;
    """

    print("\nIs it day or night? ...")
    settings = settings

    if times is None:
        if settings is None:
            raise AttributeError(
                "gnome-night-shift: unable to check `day or night`. \nMISSING required attribute `Times` (sunrise, sunset)."
            )
        times = settings.get("times")

    [sunrise, sunset] = times
    current_time = datetime.now().strftime("%H:%M")  # 24hr format

    # check if currrent time is after sunrise or sunset
    DAY_NIGHT: str

    if sunrise <= current_time < sunset:
        DAY_NIGHT = "day"
    else:
        DAY_NIGHT = "night"

    # set day-or-night
    if settings is None:
        print(
            "gnome-night-shift: unable to save day-or-night: settings unavailable",
            file=sys.stderr,
        )
    else:
        settings.set("day-or-night", DAY_NIGHT)

    print(f"{DAY_NIGHT}time")
    return DAY_NIGHT
