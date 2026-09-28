# GNOME Night Shift

Night Shift will lookup the time of the sunrise and sunset for the provided location.

- night-shift can also check if the current state of the 24hr period is day or night
- night-shift Services


## Features

* Use geoclue to determine location. Requires Location services to be enabled. **(Settings > Privacy & Security > Location > Enable "Automatic Device Location"**
* Run night-shift as a systemd service.

## How It Works

**Night Shift** can use the provided `latitude` and `longitude` OR will use `geoclue` to determine your systems geolocation.
Next **Night shift** will determine the time for sunrise and sunset.

Then **Night Shift** will attempt to create a Gsettings Object to store the data.

## Requirements

* GNOME


## Installation

### PIP

```bash
pip install gnome-night-shift
```

## Usage


```sh
usage: night-shift [-h] [-c] [-f] [-g] [-v] [--install-systemd-units]
                   [--remove-systemd-units]
                   [latitude] [longitude]

Get the times for the sunrise/sunset

positional arguments:
  latitude              compares current time with sunrise/sunset time
  longitude             compares current time with sunrise/sunset time

options:
  -h, --help            show this help message and exit
  -c, --check-now       compares current time with sunrise/sunset time
  -f, --force           ignores cached data
  -g, --geoclue         use geoclue to determine location
  -v, --verbose         Prints all data
  --install-systemd-units
                        Linux-only: Deploy optional systemd units
  --remove-systemd-units
                        Linux-only: Remove optional systemd units

```

## Source Code

* GitHub: https://github.com/christophermca/night-shift
