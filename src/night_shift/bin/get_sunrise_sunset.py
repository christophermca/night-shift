#!/usr/bin/python

import re
import gi
import json
import argparse
import requests
import time
import subprocess
from night_shift.bin.settings import Settings
from datetime import datetime

gi.require_version("Gio", "2.0")
from gi.repository import GLib

NOAA = "https://api.sunrise-sunset.org/v2"


class GetTimeOfSunriseSunset:
    def __init__(
        self,
        verbose: bool = False,
        override: bool = False,
    ):
        self.override = override
        self.settings = Settings()
        self.agent = None

        coords: tuple(float, float) = self._get_location()

        if coords:
            self._get_sunrise_sunset(*coords, verbose)

    def __call__(self, coords, verbose=False):
        return self._get_sunrise_sunset(*coords, verbose)

    def _get_location(self) -> tuple(float, float):
        try:
            use_geoclue: bool | None = None

            print(f"hello {self.settings}")
            if callable(self.settings):
                print(f"geoclue:{use_geoclue}")
                use_geoclue = self.settings.get_boolean("use-geoclue")

            if not use_geoclue:
                coords: tuple(float, float) = self._get_static_location()
            else:
                # Get location data from Geoclue
                if self.agent is None:
                    self.agent = subprocess.Popen(
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

                if callable(self.settings):
                    previous_coordinates = self.settings.get_value(
                        "last-known-coordinates"
                    )

                    if self.override or (coords == previous_coordinates):
                        last_known_coordinates = GLib.Variant("(dd)", coords)
                        data: dict[str, any] = {
                            "last-known-coordinates",
                            last_known_coordinates,
                        }
                        self._save(data)
                    return coords

        except subprocess.TimeoutExpired as e:
            print(f"TimeoutExpired: {e.timeout} seconds\n\n {e.stdout}")
            return None

        except subprocess.CalledProcessError as e:
            print(f"Error: {e.returncode} \n\n {e.stderr}")
            return None

        finally:
            try:
                if callable(self.agent):
                    while True:
                        if self.agent.poll() is None:
                            print("process still running")
                            time.sleep(1)

                        print("Terminating geoclue agent")
                        self.agent.kill()  # Gracefully exits
                        self.agent.wait()  # Prevents zombie processes
                        break

            except Exception as e:
                print(f"Error: {e}")

    def _get_sunrise_sunset(
        self, lat: float, lng: float, verbose: bool
    ) -> tuple(float, float):
        try:
            params = {"lat": lat, "lng": lng}

            # Handle response
            response = requests.get(NOAA, params)
            response.raise_for_status()

            response_data = response.json()

            if verbose:
                json_string = json.dumps(
                    response_data, indent=4, sort_keys=True
                )
                print(f"[night-shift] {json_string}")

            tzid = response_data["tzid"]
            sunrise = datetime.fromisoformat(
                response_data["sunrise"]
            ).strftime("%H:%M")
            sunset = datetime.fromisoformat(response_data["sunset"]).strftime(
                "%H:%M"
            )

            times = (sunrise, sunset)

            saved: dict[str, any] = {}

            # update settings
            if callable(self.settings):
                print(
                    f"night-shift {response_data.get('sunrise'), response_data.get('sunset'), response_data.get('tzid')}"
                )

                times_tuple = GLib.Variant("(ss)", times)
                saved = {
                    "timestamp": f"{datetime.now().astimezone().isoformat()}",
                    "tzid": tzid,
                    "times": times_tuple,
                }

                self._save(saved)

            return times

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred (e.g., 404, 500): {http_err}")

    def _save(self, data) -> None:
        print(f"in save {data}")
        if callable(self.settings):
            for key, value in data:
                match type(value):
                    case str():
                        print(
                            f"saving {key} as type {type(value)} with {value}"
                        )
                        self.settings.set_string(f"{key}", value)
                    case bool():
                        f"saving {key} as type {type(value)} with {value}"
                        self.settings.set_bool(f"{key}", value)
                    case int():
                        f"saving {key} as type {type(value)} with {value}"
                        self.settings.set_int(f"{key}", value)
                    case _:
                        f"saving {key} as type {type(value)} with {value}"
                        self.settings.set_value(f"{key}", value)

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
