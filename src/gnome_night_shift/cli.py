#!/usr/bin/python
from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from gnome_night_shift.bin.is_day_or_night import is_day_or_night
from gnome_night_shift.bin.settings import Settings
from gnome_night_shift.services import Services
from .data_store import DataStore

import sys
import argparse


def user_passes_check_now_arg(args):
    if args.check_now == None:
        return args.check_now == True


def user_passes_watch_arg(args):
    return args.watch != False


def check(times=None, settings=None):
    try:
        is_day_or_night(times, settings=settings)
    except AttributeError as e:
        print(f"{e}")


def run_once(
    verbose: bool = False,
    override: bool = False,
    check_now: bool | str | None = False,
    use_geoclue: bool = False,
    settings=None,
):
    try:
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose, override, use_geoclue, settings
        )
        if check_now != True:
            try:
                check(sunrise_sunset.times, settings)
            except Exception as e:
                print(f"check failed: {e}")

    except Exception as e:
        print(f"ERROR during run_once(): {e} ")


def main():
    parser = argparse.ArgumentParser(
        description="Get the times for the sunrise/sunset"
    )

    parser.add_argument(
        "latitude",
        type=float,
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "longitude",
        type=float,
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "-c",
        "--check-now",
        nargs="?",
        default=False,
        help="compares current time with sunrise/sunset time",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="override",
        action="store_true",
        help="ignores cached data",
    )

    parser.add_argument(
        "-g",
        "--geoclue",
        dest="use_geoclue",
        action="store_true",
        help="use geoclue to determine location",
    )

    parser.add_argument(
        "-w",
        "--watch",
        nargs="?",
        default=False,
        help="watch for changes in data_store",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Prints all data",
    )

    args = parser.parse_args()
    print(f"DEBUG: {args}")

    if user_passes_watch_arg(args):
        if args.watch == None:
            args.watch = "DEFAULT"

        # use a data_store
        data_store = DataStore(args.watch)
        settings = Settings(data_store)

        # call night-shift watching settings
        GetTimeOfSunriseSunset(args.verbose, args.override, None, settings)
        if args.check_now:
            return check(None, settings)

    elif args.latitude != None and args.longitude != None:
        # One Settings per run, shared by everything below, so a missing schema is reported once. Only created on paths that need it.
        settings = Settings()
        coords = tuple([args.latitude, args.longitude])
        sunrise_sunset = GetTimeOfSunriseSunset(
            args.verbose, args.override, settings=settings
        )
        times = sunrise_sunset(coords, args.verbose)
        if args.check_now:
            return check(times, settings)

    elif args.use_geoclue:
        return run_once(
            args.verbose,
            args.override,
            args.check_now,
            args.use_geoclue,
        )

    elif args.check_now != False:
        user_passes_check_now_arg(args)
        if type(args.check_now) is str:
            data_store = DataStore(args.check_now)
            settings = Settings(data_store)
            return check(settings=settings)

        return check(settings=None)

    else:
        parser.print_help()
