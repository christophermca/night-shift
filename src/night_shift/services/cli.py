def register(subparsers):
    """Entry point for night-shift: add the `services` command, return its handler."""
    setup_arguments(subparsers)
    return run


def run(args):
    from . import NightShiftServices

    services = NightShiftServices()
    if args.subcommand == "setup":
        return services.setup(args.schema, args.build_only)
    if args.subcommand == "start":
        return services.start()
    if args.subcommand == "stop":
        return services.stop()
    if args.subcommand == "taredown":
        return services.destroy()


def setup_arguments(subparsers):
    services_parser = subparsers.add_parser(
        "services",
        prog="night-shift services",
        help="Handle Night-Shift Service",
    )

    action_parser = services_parser.add_subparsers(
        dest="subcommand",
        prog="night-shift services",
    )

    stop_action_parser = action_parser.add_parser(
        "stop", help="Stop night-shift services"
    )

    start_action_parser = action_parser.add_parser(
        "start", help="starts night-shift services"
    )

    build_action_parser = action_parser.add_parser(
        "setup", help="builds night-shift services"
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
        default=None,
        help="Path to GObject schema",
    )

    build_action_parser = action_parser.add_parser(
        "taredown", help="removes linked systemd units"
    )
