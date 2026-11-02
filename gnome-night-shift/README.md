# gnome-night-shift

The helper for the [Night Shift GNOME extension](https://github.com/christophermca/gnome-shell-extension-night-shift):
it switches GNOME between light and dark at sunrise and sunset.

It installs [`nocturne-shift`](https://pypi.org/project/nocturne-shift/) (the `nocturne-shift`
command) and adds the systemd timers that run it, as `nocturne-shift services`:

```sh
nocturne-shift services setup [SCHEMA_PATH]   # link and start the timers
nocturne-shift services stop
nocturne-shift services start
nocturne-shift services teardown              # stop and remove the timers
```

## Install

```sh
pipx install --system-site-packages gnome-night-shift
```

`--system-site-packages` uses your distro's PyGObject instead of building it.
Requires Linux with systemd.
