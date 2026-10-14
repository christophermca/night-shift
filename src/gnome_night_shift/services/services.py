#!/usr/bin/python
import sys
import os
import subprocess
import shutil
from pathlib import Path


class Services:
    def __init__(self, source_dir="", target_dir=""):
        self.source_dir = source_dir
        self.target_dir = target_dir

        if sys.platform != "linux":
            sys.exit("Error: Systemd units can ony be deployed on linux")

        list_of_units = []
        with os.scandir(self.source_dir) as units:
            for unit in units:
                list_of_units.append(unit)

        self.all_units = list_of_units
        self.timers = [
            unit for unit in list_of_units if unit.name.endswith(".timer")
        ]

    def _symlink(self, source: str | None = None):
        source = source if source is not None else self.source_dir
        Path(self.target_dir).mkdir(parents=True, exist_ok=True)
        for unit in self.all_units:
            print(f"UNIT_PATH: {unit.name}, {source}")
            if unit.is_file():
                try:
                    source = source if source is not None else self.source_dir
                    src = f"{source}/{unit.name}"
                    target = f"{self.target_dir}/{unit.name}"
                    os.symlink(src, target)
                except FileExistsError:
                    if os.path.islink(target):
                        print(f"is link, target:{target}, src: {unit.path}")
                        os.remove(target)
                        os.symlink(src, target)
                    else:
                        print(f"skipping {unit.name} :: file exists")
                finally:
                    print("+++++")
                    print(f"SYMLINKED {unit.name}\n")

    def _create_units(self, schema=None):
        self.target_dir.mkdir(parents=True, exist_ok=True)

        # progromatically write systemd units vs copy/pasting

        if schema:
            tmp_dir = Path(__file__).parent / "tmp"
            tmp_dir.mkdir(parents=True, exist_ok=True)

            self._make_copy_of_unit(self.all_units, schema, tmp_dir)

            if any(tmp_dir.iterdir()):
                self._symlink(tmp_dir)

        else:
            self._symlink(self.source_dir)

    def _daemon_reload(self) -> None:
        try:
            subprocess.run(
                ["systemctl", "--user", "daemon-reload"], check=True
            )
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def _start_services(self):
        try:
            self._daemon_reload()

            for timer in self.timers:
                print(f"Starting timer: {timer.name}")

                subprocess.run(
                    ["systemctl", "--user", "enable", "--now", timer.name],
                    check=True,
                )
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")
        finally:
            print("\n")

    def _stop_services(self):
        try:
            self._daemon_reload()

            for timer in self.timers:
                print(f"stopping timer: {timer.name}")

                subprocess.run(
                    ["systemctl", "--user", "disable", "--now", timer.name],
                    check=True,
                )

        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def _remove_symlink(self):
        for unit in self.all_units:
            if unit.is_file():
                try:
                    target = f"{self.target_dir}/{unit.name}"
                    if os.path.islink(target):
                        os.remove(target)
                except FileNotFoundError:
                    print(f"{unit.name} was not found")
                    pass
                finally:
                    print("-----")
                    print(f"Removed {unit.name}\n")

        self._daemon_reload()

    def _make_copy_of_unit(
        self,
        units: list[str],
        schema_path: str | None,
        save_to_path: str | None,
    ) -> str | None:
        try:
            # TODO change tmp/ to a hiddle folder .tmp/

            # make copy with changes to execStart
            # save to tmp
            for unit in units:
                if unit.is_file():
                    file_copy = shutil.copy2(unit, save_to_path)
                    with open(unit, "r", encoding="utf-8") as file:
                        lines = file.readlines()

                        for i, line in enumerate(lines):
                            if line.startswith("ExecStart="):
                                words = [line.strip(), schema_path]
                                lines[i] = f"{line.rstrip()} {schema_path}\n"

                        with open(file_copy, "w") as file:
                            file.writelines(
                                lines
                            )  # overwrites files in tmp_dir

        except Exception:
            return None

    # PUBLIC API
    def setup(
        self,
        schema_path=None,
        build_only=False,
    ):
        self._create_units(schema_path)
        if build_only is False:
            self.start()

    def start(self):
        self._start_services()

    def stop(self):
        self._stop_services()

    def destroy(self):
        self.stop()
        self._remove_symlink()
