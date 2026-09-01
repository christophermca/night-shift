# GNOME Night Shift

GNOME Night Shift is a utility that automatically switches your desktop between **Day** and **Night** modes (Light and Dark themes). Instead of manually changing appearance settings, the utility detects whether it is currently day or night at your location and applies the appropriate mode automatically.

 night shift is designed for users who prefer a light desktop during the day and a dark desktop after sunset, providing a seamless transition throughout the day.

## Features

* Automatically switch between **Day** (Light) and **Night** (Dark) modes.
* Uses sunrise and sunset times for your location.
* Integrates directly with GNOME Shell.
* Lightweight and easy to configure.

## How It Works

GNOME night Shift relies on **Redshift** to determine whether the sun is currently above or below the horizon at your location.

Your geographic location is configured through Redshift's configuration file. Using this information, Redshift calculates local sunrise and sunset times, allowing GNOME Mode Shift to determine when to activate **Day** or **Night** mode.

The extension does **not** determine your location on its own—it uses the location configured for Redshift.

## Requirements

* GNOME
* Redshift
* A configured Redshift location (latitude and longitude or another supported location provider)

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

1. Install and configure **Redshift** with your location.
2. Install and enable **GNOME Mode Shift** i.e. (`systemctl enable --now gnome-night-shift.service`)
3. Configure the appearance settings for **Day** mode.
4. Configure the appearance settings for **Night** mode.
5. The extension will automatically switch modes based on the current sunrise and sunset times reported by Redshift.

Once configured, GNOME Mode Shift automatically changes between Day and Night modes as sunrise and sunset occur at your configured location.

## Source Code

* GitHub: https://github.com/christophermca/gnome-night-shift
* Arch Linux (AUR): https://aur.archlinux.org/packages/gnome-night-shift-git

## License

# GNOME Mode Shift

GNOME Mode Shift is a GNOME Shell extension that automatically switches your desktop between **Day** and **Night** modes (Light and Dark themes). Instead of manually changing appearance settings, the extension detects whether it is currently day or night at your location and applies the appropriate mode automatically.

The extension is designed for users who prefer a light desktop during the day and a dark desktop after sunset, providing a seamless transition throughout the day.

## Features

* Automatically switch between **Day** (Light) and **Night** (Dark) modes.
* Uses sunrise and sunset times for your location.
* Integrates directly with GNOME Shell.
* Lightweight and easy to configure.

## How It Works

GNOME Mode Shift relies on **Redshift** to determine whether the sun is currently above or below the horizon at your location.

Your geographic location is configured through Redshift's configuration file. Using this information, Redshift calculates local sunrise and sunset times, allowing GNOME Mode Shift to determine when to activate **Day** or **Night** mode.

The extension does **not** determine your location on its own—it uses the location configured for Redshift.

## Requirements

* GNOME
* Redshift
* A configured Redshift location (latitude and longitude or another supported location provider)

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

1. Install and configure **Redshift** with your location.
2. Install and enable **GNOME Night Shift**
```sh
systemctl enable --now gnome-night-shift.service gnome-night-shift.timer auto-update-gnome-theme.service auto-update-gnome-theme.path stop-mode-shift-timer.service
```
3. Configure the appearance settings for **Day** mode.ti
4. Configure the appearance settings for **Night** mode.
5. The extension will automatically switch modes based on the current sunrise and sunset times reported by Redshift.

Once configured, GNOME Night Shift automatically changes between Day and Night modes as sunrise and sunset occur at your configured location.

## Source Code

* GitHub: https://github.com/christophermca/gnome-night-shift
* Arch Linux (AUR): https://aur.archlinux.org/packages/gnome-night-shift-git
