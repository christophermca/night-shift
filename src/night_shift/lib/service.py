#!/usr/bin/python
import sys
import os
import subprocess
from pathlib import Path

package_dir = Path(__file__).parent.parent
systemd_dir = package_dir / "systemd" / "user"

target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


class Services:
    def __init__(self):
        if sys.platform != "linux":
            sys.exit("Error: Systemd units can ony be deployed on linux")

        list_of_units = []
        with os.scandir(systemd_dir) as units:
            for unit in units:
                list_of_units.append(unit)

        self.all_units = list_of_units
        self.timers = [
            unit for unit in list_of_units if unit.name.endswith(".timer")
        ]

    def _symlink(self):
        target_dir.mkdir(parents=True, exist_ok=True)

        with os.scandir(systemd_dir) as units:
            for unit in self.all_units:
                if unit.is_file():
                    try:
                        target = f"{target_dir}/{unit.name}"
                        os.symlink(unit.path, target)
                    except FileExistsError:
                        if os.path.islink(target):
                            os.remove(target)
                            os.symlink(unit.path, target)
                        else:
                            print(f"skipping {unit.name} :: file exists")
                    finally:
                        print(f"SYMLINKED {unit.name}")
                        print("+++++\n")

    def _start_services(self):
        try:
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"], check=True
            )

            for timer in self.timers:
                print(f"unit-name: {timer.name}")

            subprocess.run(
                ["systemctl", "--user", "enable", "--now", timer.name],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def _stop_services(self):
        try:
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"], check=True
            )

            for timer in self.timers:
                print(f"unit-name: {timer.name}")

            subprocess.run(
                ["systemctl", "--user", "disable", "--now", timer.name],
                check=True,
            )

        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def _remove_symlink(self):
        for unit in self.units:
            if unit.is_file():
                try:
                    target = f"{target_dir}/{unit.name}"
                    if os.path.islink(target):
                        os.remove(target)
                        print(f"Removed {unit.name}")
                except FileNotFoundError:
                    print(f"{unit.name} was not found")
                    pass
                finally:
                    print("-----\n")

    def setup(self):
        self._symlink()
        self._start_services()

    def stop(self):
        self._stop_services()

    def destroy(self):
        self.stop()
        self._remove_symlink()


if __name__ == "__main__":
    Services()
