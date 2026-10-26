#!/usr/bin/python

import sys

from night_shift.bin.settings import Settings
from datetime import datetime


def is_day_or_night(
    times: tuple[str, str] | None = None,
    settings: Settings | None = None,
    verbose=0,
):
    """Work out "day" or "night" and save it.

    `times` is a (sunrise, sunset) pair of "HH:MM" strings. When it's not
    given, the times saved in settings are used.

    `settings` is a `Settings`. When it's not given, raise an Error to the caller;
    """

    settings = settings

    if times is None:
        if settings is None:
            raise AttributeError(
                "night-shift: unable to check `day or night`. settings is None"
            )
            return

        times = settings.get("times")

    if not times:
        return
    [sunrise, sunset] = times
    current_time = datetime.now().strftime("%H:%M")  # 24hr format

    # check if currrent time is after sunrise or sunset
    DAY_NIGHT: str

    if verbose >= 1:
        print(sunrise, current_time, sunset)

    if sunrise <= current_time < sunset:
        DAY_NIGHT = "day"
    else:
        DAY_NIGHT = "night"

    # set day-or-night
    try:
        settings.set("day-or-night", DAY_NIGHT)
    except Exception as e:
        print(
            "night-shift: unable to save day-or-night: settings unavailable",
            file=sys.stderr,
        )

    print(f"{DAY_NIGHT}")
    return DAY_NIGHT
