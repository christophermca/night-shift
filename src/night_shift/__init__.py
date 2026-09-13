#!/usr/bin/python
from night_shift.bin.get_sunrise_sunset import main as get_sunrise_sunset_times
import night_shift.lib.service as service


def destroy():
    service.destroy()


def setup():
    service.setup()


def run_once():
    get_sunrise_sunset_times()


if __name__ == "__main__":
    run_once()
