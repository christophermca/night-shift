import importlib.metadata

try:
    __version__ = importlib.metadata.version("night_shift_services")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"


def register(subparsers):
    """Entry point for night-shift: add the `services` command, return its handler."""
    services_parser = setup_arguments(subparsers)

    def handler(args):
        if args.subcommand is None:  # bare `night-shift services`
            services_parser.print_help()
            return None  # nothing was done
        return run(args)

    return handler


def run(args):
    from . import NightShiftServices

    services = NightShiftServices()
    if args.subcommand == "setup":
        return services.setup(args.schema, args.build_only)
    elif args.subcommand == "start":
        return services.start()
    elif args.subcommand == "stop":
        return services.stop()
    elif args.subcommand == "teardown":
        return services.destroy()


def setup_arguments(subparsers):
    services_parser = subparsers.add_parser(
        "services",
        prog="night-shift services",
        help="Handle Night-Shift Service",
    )

    services_parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Prints more information",
    )

    action_parser = services_parser.add_subparsers(
        dest="subcommand",
        prog="night-shift services",
    )

    stop_action_parser = action_parser.add_parser(
        "stop", help="Stops night-shift services"
    )

    start_action_parser = action_parser.add_parser(
        "start", help="Starts night-shift services"
    )

    build_action_parser = action_parser.add_parser(
        "setup", help="Builds night-shift services"
    )

    build_action_parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build service units",
    )

    build_action_parser.add_argument(
        "schema",
        type=str,
        action="store",
        nargs="?",
        help="Path to GObject schema",
    )

    teardown_action_parser = action_parser.add_parser(
        "teardown", help="Removes linked systemd units"
    )

    return services_parser
