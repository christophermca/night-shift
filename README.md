# GNOME Night Shift

GNOME Night Shift is a GNOME Shell extension that automatically switches your desktop between **Day** and **Night** modes (Light and Dark themes). Instead of manually changing appearance settings, the extension detects whether it is currently day or night at your location and applies the appropriate mode automatically.

The extension is designed for users who prefer a light desktop during the day and a dark desktop after sunset, providing a seamless transition throughout the day.

## Features

* Automatically switch between **Day** (Light) and **Night** (Dark) modes.
* Uses sunrise and sunset times for your location. Requires Location services to be enabled. **(Settings > Privacy & Security > Location > Enable "Automatic Device Location"**
* Integrates directly with GNOME Shell.
* Lightweight and easy to configure.

## How It Works

GNOME Night Shift uses on Gnome's **Location services* to get your geolocation, then looks up what time the sun will rise and set.

## Requirements

* GNOME


## Installation

### Arch Linux

The latest development version is available from the Arch User Repository (AUR):

```bash
yay -S gnome-night-shift-git
```

or

```bash
paru -S gnome-night-shift-git
```

## Usage


2. Install and enable **GNOME Ngiht Shift** i.e. (`systemctl --user enable --now gnome-night-shift.timer get-sunrise-sunset.timer auto-update-gnome-theme`)
5. The extension will automatically switch modes based on the current sunrise and sunset times.

Once configured, GNOME night Shift automatically changes between Day and Night modes as sunrise and sunset occur at your geolocation.

## Source Code

* GitHub: https://github.com/christophermca/gnome-night-shift
* Arch Linux (AUR): https://aur.archlinux.org/packages/gnome-night-shift-git

