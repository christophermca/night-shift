#!/usr/bin/python
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from night_shift.bin.is_day_or_night import is_day_or_night
from night_shift.lib.service import Services
import sys
import argparse


def check():
    is_day_or_night()


def run_once(
    verbose: bool = False,
    override: bool = False,
    check_now: bool = False,
    use_geoclue: bool = False,
):
    try:
        GetTimeOfSunriseSunset(verbose, override, use_geoclue)
        if check_now == True:
            try:
                check()
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
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "longitude",
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "-c",
        "--check-now",
        action="store_true",
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
        "-v",
        "--verbose",
        action="store_true",
        help="Prints all data",
    )
    parser.add_argument(
        "--install-systemd-units",
        action="store_true",
        help="Linux-only: Deploy optional systemd units",
    )
    parser.add_argument(
        "--remove-systemd-units",
        action="store_true",
        help="Linux-only: Remove optional systemd units",
    )

    args = parser.parse_args()

    if sys.platform == "linux":
        if args.install_systemd_units:
            return Services().setup()
        elif args.remove_systemd_units:
            return Services().destroy()

    if args.latitude is not None and args.longitude is not None:
        coords = tuple([args.latitude, args.longitude])
        sunrise_sunset = GetTimeOfSunriseSunset(args.verbose, args.override)
        return sunrise_sunset(coords, args.verbose)

    elif args.use_geoclue:
        print("should use geoclue")
        return run_once(
            args.verbose, args.override, args.check_now, args.use_geoclue
        )

    elif args.check_now:
        return check()

    else:
        parser.print_help()
