#!/usr/bin/python

from night_shift.bin.settings import Settings
from datetime import datetime


def is_day_or_night():
    print("is_day_or_night")
    settings = Settings()()

    times: list[str] = settings.get_value("times")

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
