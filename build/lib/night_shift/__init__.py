#!/usr/bin/python
import night_shift.bin.get_sunrise_sunset as get_sunrise_sunset_times
import night_shift.lib.service as service


def destroy():
    service.destroy()


def setup():
    service.setup()


def run_once():
    get_sunrise_sunset_times()


if __name__ == "__main__":
    run_once()
