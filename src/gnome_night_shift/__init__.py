#!/usr/bin/python
from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from gnome_night_shift.bin.is_day_or_night import is_day_or_night
from gnome_night_shift.bin.settings import Settings
from gnome_night_shift.lib.service import Services

import sys
import argparse


def check(times=None, settings=None):
    # Returns None on purpose: the console script does sys.exit(main()).
    is_day_or_night(times, settings)


def run_once(
    verbose: bool = False,
    override: bool = False,
    check_now: bool = False,
    use_geoclue: bool = False,
    settings=None,
):
    try:
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose, override, use_geoclue, settings=settings
        )
        if check_now == True:
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
        from pathlib import Path

        package_dir = Path(__file__).parent
        systemd_dir = package_dir / "systemd" / "user"

        target_dir = Path.home() / ".local" / "share" / "systemd" / "user"
        services = Services(systemd_dir, target_dir)

        if args.install_systemd_units:
            return services.setup()
        elif args.remove_systemd_units:
            return services.destroy()

    if args.latitude is not None and args.longitude is not None:
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
            settings=Settings(),
        )

    elif args.check_now:
        return check(settings=Settings())

    else:
        parser.print_help()
