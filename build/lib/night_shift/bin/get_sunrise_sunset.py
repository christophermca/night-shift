#!/usr/bin/python

import re
import gi
import json
import argparse
import requests
import subprocess

from datetime import datetime

gi.require_version("Gio", "2.0")
from gi.repository import GLib

NOAA = "https://api.sunrise-sunset.org/v2"


class Settings:

    def __init__(self):
        import os
        from pathlib import Path
        from gi.repository import Gio

        # Load schema
        SCHEMA_ID = "org.gnome.shell.extensions.night-shift"

        schema_dir = os.path.expanduser(
            Path.home()
            / ".local"
            / "share"
            / "gnome-shell"
            / "extensions"
            / "night-shift@christophermca.github.io"
            / "schemas"
        )

        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_dir, Gio.SettingsSchemaSource.get_default(), False
        )

        try:
            # initialize gsettings obj
            schemaObj = schema_source.lookup(SCHEMA_ID, True)
            settings = Gio.Settings.new_full(schemaObj, None, None)

            self.settings = settings

        except Exception as e:
            print(f"Error {e}")
            return None


class GetTimeOfSunriseSunset:
    def __init__(
        self,
        debug: bool = False,
        override: bool = False,
        lat_lng: tuple(float, float) = None,
    ):
        self.settings = Settings()
        self.agent = None
        coords: tuple(float, float) = (
            lat_lng if lat_lng else self._get_location(override)
        )

        if coords:
            self._get_sunrise_sunset(*coords, debug)

    def _get_location(self, override: bool) -> tuple(float, float):
        try:
            useGeoclue: bool | None = None
            if callable(self.settings):
                useGeoclue = self.settings.get_boolean("use-geoclue")

            if useGeoclue:
                coords: tuple(float, float) = _get_static_location()
            else:
                # Get location data from Geoclue
                if self.agent is not None and agent.poll() is None:
                    agent = subprocess.Popen(
                        ["/usr/lib/geoclue-2.0/demos/agent"]
                    )
                geoclue_data = subprocess.Popen(
                    [
                        "/usr/lib/geoclue-2.0/demos/where-am-i",
                        "--accuracy-level=8",
                        "--time-threshold=3",
                    ],  # `run /usr/lib/geoclue-2.0/demo/where-am-i -h` for more information about options
                    text=True,
                    stdout=subprocess.PIPE,
                )

                regex = r"^(Lat.*:|Long.*:).*([\.\-\d+]+)"
                timestamp = r"^(Timestamp:).*([\.\-\d+]+)"

                # READS response for LAT and LNG
                arr = []

                for line in iter(geoclue_data.stdout.readline, ""):
                    match = re.match(regex, line)

                    if match:
                        matched_string = match.group().split()[1]
                        arr.append(float(matched_string))

                    if len(arr) == 2:
                        geoclue_data.terminate()
                        break

                if not arr:
                    raise TypeError(
                        "Could not determine location. Please check your geoclue configuration"
                    )
                coords = tuple(arr)

                self._save(coords, override)

            return coords

        except subprocess.TimeoutExpired as e:
            print(f"TimeoutExpired: {e.timeout} seconds\n\n {e.stdout}")
            return None

        except subprocess.CalledProcessError as e:
            print(f"Error: {e.returncode} \n\n {e.stderr}")
            return None

        finally:
            try:
                while agent.poll() is None:
                    print("process still running")
                    time.sleep(1)

                print("Terminating geoclue agent")
                agent.terminate()  # Gracefully exits
                agent.wait()  # Prevents zombie processes

            except NameError:
                pass

    def _get_sunrise_sunset(
        self, lat: float, lng: float, debug: bool
    ) -> tuple(float, float):
        try:
            params = {"lat": lat, "lng": lng}

            # Handle response
            response = requests.get(NOAA, params)
            response.raise_for_status()

            data = response.json()

            if debug:
                json_string = json.dumps(data, indent=4, sort_keys=True)
                print(f"[night-shift] {json_string}")

            tzid = data["tzid"]
            sunrise = datetime.fromisoformat(data["sunrise"]).strftime("%H:%M")
            sunset = datetime.fromisoformat(data["sunset"]).strftime("%H:%M")

            times = (sunrise, sunset)

            # update settings
            if callable(self.settings):
                self.settings.set_string(
                    "timestamp", f"{datetime.now().astimezone().isoformat()}"
                )
                print(
                    f"night-shift {data.get('sunrise'), data.get('sunset'), data.get('tzid')}"
                )
                self.settings.set_string("tzid", tzid)
                times_tuple = GLib.Variant("(ss)", times)
                self.settings.set_value("times", times_tuple)

            return times

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred (e.g., 404, 500): {http_err}")

    def _save(self, coords: tuple(float, float), override=False) -> None:
        if callable(self.settings):
            previous_coordinates = self.settings.get_value(
                "last-known-coordinates"
            )

            if override or (coords == previous_coordinates):

                last_known_coordinates = GLib.Variant("(dd)", coords)
                self.settings.set_value(
                    "last-known-coordinates", last_known_coordinates
                )
                return coords
            else:
                coords_string = ",".join(map(str, coords))
                print(
                    f"Locations are the same (old/new) '{previous_coordinates}'/'{coords_string}'"
                )

    def _get_static_location(self) -> tuple(float, float):

        if callable(self.settings):
            lat = self.settings.get_string("static-latitude")
            lng = self.settings.get_string("static-longitude")

            if lat and lng:
                static_location = (float(lat), float(lng))

                last_known_coordinates = GLib.Variant("(dd)", static_location)
                self.settings.set_value(
                    "last-known-coordinates", last_known_coordinates
                )

                return static_location

            else:
                print("Missing required keys")
