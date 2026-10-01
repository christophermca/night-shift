from pathlib import Path
from .services import Services

service_module_dir = Path(__file__).parent
source_units_dir = service_module_dir / "systemd" / "user"

target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


class NightShiftServices(Services):
    def __init__(
        self,
        source_dir=source_units_dir,
        target_dir=target_dir,
        schema=None,
    ):
        self.schema_path = schema
        super().__init__(source_dir, target_dir)

    def setup(self, schema_path, build_only):
        return super().setup(schema_path, build_only)

    def start(self):
        super().start()

    def stop(self):
        super().stop()

    def destroy(self):
        super().destroy()


def setup_arguments(subparsers):
    services_parser = subparsers.add_parser(
        "services", help="handle Night-Shift Service"
    )

    services_parser.add_argument(
        "schema",
        type=str,
        action="store",
        default=None,
        help="Path to GObject schema",
    )

    action_parser = services_parser.add_subparsers(
        dest="subcommand",
        title="Actions",
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
