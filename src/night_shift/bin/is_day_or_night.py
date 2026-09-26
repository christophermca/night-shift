#!/usr/bin/python

import sys

from night_shift.bin.settings import Settings
from datetime import datetime


def is_day_or_night(times=None):
    """Work out "day" or "night" and save it.

    `times` is a (sunrise, sunset) pair of "HH:MM" strings. When it's not
    given, the times saved in settings are used.
    """
    print("is_day_or_night")
    settings = Settings()()

    if times is None:
        if settings is None:
            print(
                "night-shift: unable to check day or night: no saved sunrise/sunset times",
                file=sys.stderr,
            )
            return None
        times = settings.get_value("times")

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
            "night-shift: unable to save day-or-night: settings unavailable",
            file=sys.stderr,
        )
    else:
        settings.set_string("day-or-night", DAY_NIGHT)

    print(f"{DAY_NIGHT}time")
    return DAY_NIGHT
