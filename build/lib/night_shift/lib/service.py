#!/usr/bin/python
from pathlib import Path
import os

package_dir = Path(__file__).parent.parent
systemd_dir = package_dir / "systemd" / "user"
target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


class Services:
    def _symlink(self):
        target_dir.mkdir(parents=True, exist_ok=True)
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

    def _start_services(self):
        print("start_service")
        pass

    def _stop_services(self):
        pass

    def _remove_symlink(self):
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

    def setup(self):
        self._symlink()
        self._start_services()

    def stop(self):
        self._stop_services()

    def destroy(self):
        self._stop_services()
        self._remove_symlink()


if __name__ == "__main__":
    Service()
