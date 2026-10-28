#!/usr/bin/python
# PYTHON_ARG_COMPLETE_OK
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from night_shift.bin.is_day_or_night import is_day_or_night
from night_shift.bin.settings import Settings
from night_shift.services import NightShiftServices, setup_arguments
from .data_store import DataStore

import sys
import argparse
import argcomplete
import importlib.metadata
from importlib.util import find_spec

try:
    __version__ = importlib.metadata.version("night_shift_cli")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


def check(times=None, settings=None, verbose=0):
    try:
        is_day_or_night(times, settings, verbose)
    except AttributeError as e:
        print(f"ERROR: {e}")


def run_once(
    verbose: int = 0,
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
                check(sunrise_sunset.times, settings, verbose)
            except Exception as e:
                print(f"check failed: {e}")
    except Exception as e:
        print(f"ERROR during run_once(): {e} ")


def feature_check(name):
    if name == "services":
        return _is_module_installed("cairo")


def _is_module_installed(
    module_name: str,
) -> bool:
    result = importlib.util.find_spec(module_name)
    return result is not None


def main():
    parser = argparse.ArgumentParser(
        description="Get the times for the sunrise/sunset",
        prog="night-shift",
    )

    # Optionally displays help infomation if pip sub package [services] was
    # installed
    sub_parser_help = None if feature_check("services") else argparse.SUPPRESS

    sub_parsers = parser.add_subparsers(dest="command", help=sub_parser_help)

    setup_arguments(sub_parsers)

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
        action="count",
        default=0,
        help="Prints more information",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Prints more information",
    )

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # ------------ Services
    if args.command == "services":

        if feature_check("services"):
            night_shift_services = NightShiftServices()
            if args.subcommand == "setup":
                pass
                # return night_shift_services.setup(args.schema, args.build_only)
            elif args.subcommand == "start":
                return night_shift_services.start()
            elif args.subcommand == "stop":
                return night_shift_services.stop()
            elif args.subcommand == "taredown":
                return night_shift_services.destroy()
        else:
            parser.exit(
                1, "services requires: pip install `night-shift[services]`\n\n"
            )

    # ------------ Watch
    if args.watch != False:
        settings = (
            Settings(DataStore(args.watch)) if args.watch else Settings()
        )

        # TODO validate using run_once will work here.
        return run_once(
            verbose=args.verbose,
            override=args.override,
            check_now=False,  # the watch option only gets the current location if location has changed for an OVERRIDE flag was passed
            use_geoclue=None,  # watch will handle use settings
            settings=settings,
        )

    # ------------ Static coordinates
    elif args.latitude != None and args.longitude != None:
        # One Settings per run, shared by everything below, so a missing schema is reported once. Only created on paths that need it.
        settings = Settings()
        coords = tuple([args.latitude, args.longitude])
        sunrise_sunset = GetTimeOfSunriseSunset(
            args.verbose, args.override, settings=settings
        )
        times = sunrise_sunset(coords, args.verbose)
        if args.check_now != False:
            return check(times, settings, args.verbose)

    # ------------ Using Geoclue
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

        def get_settings() -> Settings:
            if not feature_check("services"):
                return Settings()
            else:
                if type(args.check_now) is str:
                    data_store = DataStore(args.check_now)
                    return Settings(data_store)
                else:
                    return Settings()

        settings = get_settings()

        check(settings=settings, verbose=args.verbose)
        return None
    else:
        parser.print_help()
