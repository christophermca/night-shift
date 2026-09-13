#!/usr/bin/python
from night_shift.bin.get_sunrise_sunset import main as get_sunrise_sunset_times
from pathlib import Path
import os

package_dir = Path(__file__).parent.parent
systemd_dir = package_dir / "systemd" / "user"
target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


def setup():
    _symlink()


def _symlink():
    target_dir.mkdir(parents=True, exist_ok=True)
    # SYMLINK units
    with os.scandir(systemd_dir) as units:
        for unit in units:
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


def destroy():
    with os.scandir(systemd_dir) as units:
        for unit in units:
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


def run_once():
    get_sunrise_sunset_times()
