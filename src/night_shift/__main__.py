#!/usr/bin/python
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
import argparse


def run_once(args=None):
    GetTimeOfSunriseSunset(**vars(args))


if __name__ == "__main__":
    # Parse commendline arguments
    parser = argparse.ArgumentParser(
        description="Get the times for the sunrise/sunset"
    )
    parser.add_argument("-f", "--force", dest="override", action="store_true")
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    run_once(args)
