from pathlib import Path
import argparse
from .services import Services

package_dir = Path(__file__).parent
systemd_dir = package_dir / "systemd" / "user"

target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


class NightShiftServices(Services):
    def __init__(
        self,
        source_dir=systemd_dir,
        target_dir=target_dir,
        schema=None,
    ):
        print(
            f"source: {source_dir}, target: { target_dir }, schema: {schema}"
        )
        self.schema_path = schema
        super().__init__(source_dir, target_dir)

    def setup(self):
        super().setup(self.schema_path)

    def stop(self):
        super().stop()

    def destroy(self):
        super().destroy()


parser = argparse.ArgumentParser(description="handle Night-shift services")

parser.add_argument("schema", type=str, action="store", default=None)

args = parser.parse_args()


print(args)
service = NightShiftServices(systemd_dir, target_dir, args.schema)


def setup():
    service.setup()


def stop():
    service.setup()


def destroy():
    service.setup()
