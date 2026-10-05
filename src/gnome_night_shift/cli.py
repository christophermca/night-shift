#!/usr/bin/python
# PYTHON_ARG_COMPLETE_OK
from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from gnome_night_shift.bin.is_day_or_night import is_day_or_night
from gnome_night_shift.bin.settings import Settings
from gnome_night_shift.services import NightShiftServices, setup_arguments
from .data_store import DataStore

import sys
import argparse
import argcomplete


def check(times=None, settings=None):
    try:
        is_day_or_night(times, settings=settings)
    except AttributeError as e:
        print(f"{e}")


def run_once(
    verbose: bool = False,
    override: bool = False,
    check_now: bool | str | None = False,
    use_geoclue: bool | None = False,
    settings: Settings | None = None,
):
    try:
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose, override, use_geoclue, settings
        )
        if check_now != False:
            try:
                check(sunrise_sunset.times, settings)
            except Exception as e:
                print(f"check failed: {e}")
    except Exception as e:
        print(f"ERROR during run_once(): {e} ")


def main():
    parser = argparse.ArgumentParser(
        description="Get the times for the sunrise/sunset",
        prog="night-shift",
    )

    services_parser = parser.add_subparsers(
        dest="command",
        title="services",
        description="valid commands",
    )

    setup_arguments(services_parser)

    parser.add_argument(
        "--lat",
        dest="latitude",
        type=float,
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "--lng",
        dest="longitude",
        type=float,
        nargs="?",
        help="compares current time with sunrise/sunset time",
    )

    parser.add_argument(
        "-c",
        "--check-now",
        metavar="SCHEMA_PATH",
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
        metavar="SCHEMA_PATH",
        help="watch for changes in data_store",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Prints all data",
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    if args.command == "services":
        night_shift_services = NightShiftServices()
        if args.subcommand == "setup":
            return night_shift_services.setup(args.schema, args.build_only)
        elif args.subcommand == "start":
            return night_shift_services.start()
        elif args.subcommand == "stop":
            return night_shift_services.stop()
        elif args.subcommand == "taredown":
            return night_shift_services.destroy()

    if args.watch != False:
        if args.watch == None:
            args.watch = "DEFAULT"

        # use a data_store
        data_store = DataStore(args.watch)
        settings = Settings(data_store)

        # TODO validate using run_once will work here.
        run_once(args.verbose, args.override, args.check_now, None, settings)

    elif args.latitude != None and args.longitude != None:
        # One Settings per run, shared by everything below, so a missing schema is reported once. Only created on paths that need it.
        settings = Settings()
        coords = tuple([args.latitude, args.longitude])
        sunrise_sunset = GetTimeOfSunriseSunset(
            args.verbose, args.override, settings=settings
        )
        times = sunrise_sunset(coords, args.verbose)
        if args.check_now != False:
            return check(times, settings)

    elif args.use_geoclue:
        settings = Settings()
        return run_once(
            args.verbose,
            args.override,
            args.check_now,
            args.use_geoclue,
            settings,
        )

    elif args.check_now != False:
        settings: Settings | None = None
        if type(args.check_now) is str:
            data_store = DataStore(args.check_now)
            settings = Settings(data_store)
            return check(settings=settings)

        check(settings=Settings())
        return None
    else:
        parser.print_help()
