def setup_arguments(subparsers):
    services_parser = subparsers.add_parser(
        "services", help="handle Night-Shift Service"
    )

    action_parser = services_parser.add_subparsers(
        dest="subcommand",
        title="sub-commands",
        metavar="",
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
