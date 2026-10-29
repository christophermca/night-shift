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
    print(args)
    from . import NightShiftServices

    services = NightShiftServices()
    if args.subcommand == "setup":
        return services.setup(args.schema, args.build_only)
    elif args.subcommand == "start":
        return services.start()
    elif args.subcommand == "stop":
        return services.stop()
    elif args.subcommand == "taredown":
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

    return services_parser
