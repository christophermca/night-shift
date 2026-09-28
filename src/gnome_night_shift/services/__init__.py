from .services import Services

from pathlib import Path

package_dir = Path(__file__).parent
systemd_dir = package_dir / "systemd" / "user"

target_dir = Path.home() / ".local" / "share" / "systemd" / "user"

services = Services(systemd_dir, target_dir)


def setup():
    services.setup()


def stop():
    services.stop()


def destroy():
    services.destroy()
