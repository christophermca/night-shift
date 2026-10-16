#!/usr/bin/python

import re
import gi
import pprint
import json
import argparse
import requests
import subprocess
import sys
from collections import namedtuple
from typing import Any
from night_shift.bin.settings import Settings
from datetime import datetime

gi.require_version("Gio", "2.0")
from gi.repository import GLib

NOAA = "https://api.sunrise-sunset.org/v2"


class GetTimeOfSunriseSunset:
    def __init__(
        self,
        verbose: int = 0,
        override: bool = False,
        use_geoclue: bool | None = False,
        settings: Settings | None = None,
    ):
        self.override = override
        self.verbose = verbose
        self.use_geoclue = use_geoclue
        self.settings = settings
        self.agent = None
        self.times: tuple[str, str] | None = None

        coords: tuple[float, float] | None

        # set coords
        if self.use_geoclue is None and self.settings is not None:
            self.use_geoclue = self.settings.get("use-geoclue")

        if self.use_geoclue is True:
            coords = self._get_location()
        else:
            coords = self._get_static_location_from_settings()

        # set times
        if coords:
            self.times = self._get_sunrise_sunset(*coords, self.verbose)

    # pass coords from cli to module
    def __call__(self, coords, verbose=0):
        return self._get_sunrise_sunset(*coords, verbose)

    def _get_location(self) -> tuple[float, float]:
        try:

            # Get location data from Geoclue
            if self.agent is None:
                self.agent = subprocess.Popen(
                    ["/usr/lib/geoclue-2.0/demos/agent"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
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

            lat_regex = r"^(Lat.*:).*([\.\-\d+]+)"
            lng_regex = r"^(Long.*:).*([\.\-\d+]+)"

            # READS response for LAT and LNG
            Coordinates = namedtuple("Coordinates", ["latitude", "longitude"])
            found_coords: dict[str, float | None] = {
                "lat": None,
                "lng": None,
            }

            for line in iter(geoclue_data.stdout.readline, ""):
                found_lat = re.match(lat_regex, line)
                found_lng = re.match(lng_regex, line)

                if found_lat:
                    matched_string = found_lat.group().split()[1]
                    found_coords["lat"] = float(matched_string)

                if found_lng:
                    matched_string = found_lng.group().split()[1]
                    found_coords["lng"] = float(matched_string)

                # attempt to exit early
                if found_coords["lat"] and found_coords["lng"]:
                    break

            geoclue_data.terminate()
            # raise exception if unable to determine coords
            if found_coords["lat"] is None and found_coords["lng"] is None:
                raise TypeError(
                    "Could not determine location. Please check your geoclue configuration"
                )

            coords = Coordinates(found_coords["lat"], found_coords["lng"])

            previous_coordinates = None
            if self.settings is not None:
                previous_coordinates = self.settings.get(
                    "last-known-coordinates"
                )
                try:
                    previous_coordinates
                except Exception as e:
                    print(f"{e}")

            # CHECK if should save?
            if self.override or (list(coords) != previous_coordinates):
                last_known_coordinates = GLib.Variant("(dd)", coords)
                data: dict = {
                    "last-known-coordinates": last_known_coordinates,
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
                if self.agent is not None:
                    self.agent.kill()  # Gracefully exits
                    self.agent.wait()  # Prevents zombie processes
                    self.agent = None

            except Exception as e:
                print(f"Error: {e}")

    def _get_sunrise_sunset(
        self, lat: float, lng: float, verbose: int
    ) -> tuple[float, float]:
        try:
            params = {"lat": lat, "lng": lng}

            # Handle response
            response = requests.get(NOAA, params)
            response.raise_for_status()

            response_data = response.json()

            if self.verbose > 1:
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

            saved: dict[str, Any] = {}

            times_tuple = GLib.Variant("(ss)", times)
            saved = {
                "timestamp": f"{datetime.now().astimezone().isoformat()}",
                "tzid": tzid,
                "times": times_tuple,
            }

            self._save(saved)

            return times

        except Exception as e:
            print(f" Generic: {e}")
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred (e.g., 404, 500): {http_err}")

    def _save(self, data) -> None:
        if self.settings is None:
            raise (
                f"night-shift: unable to save {', '.join(data)}: self.settings unavailable",
            )

        try:
            for key, value in data.items():

                match value:
                    case str():
                        self.settings.set(key, value)
                    case bool():
                        self.settings.set(key, value)
                    case int():
                        self.settings.set(key, value)
                    case _:
                        self.settings.set(key, value)

            if self.verbose > 0:
                pprint.pprint(data)

        except Exception as e:
            print(f"ERROR SAVING {e}")

    def _get_static_location_from_settings(self) -> tuple[float, float]:

        if self.settings is None:
            print(
                "night-shift: no static location: self.settings unavailable",
                file=sys.stderr,
            )
            return None

        lat = self.settings.get("static-latitude")
        lng = self.settings.get("static-longitude")

        if lat and lng:
            static_location = (float(lat), float(lng))

            last_known_coordinates = GLib.Variant("(dd)", static_location)
            self._save({"last-known-coordinates": last_known_coordinates})

            return static_location

        else:
            print("Missing required keys")
