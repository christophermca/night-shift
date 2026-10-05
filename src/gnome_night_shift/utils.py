from gnome_night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
from gnome_night_shift.bin.is_day_or_night import is_day_or_night


def user_passes_check_now_arg(args):
    if args.check_now == None:
        return args.check_now == True


def user_passes_watch_arg(args):
    return args.watch != False


def check(times=None, settings=None):
    try:
        is_day_or_night(times, settings=settings)
    except AttributeError as e:
        print(f"{e}")


def run_once(
    verbose: bool = False,
    override: bool = False,
    check_now: bool | str | None = False,
    use_geoclue: bool = False,
    settings=None,
):
    try:
        sunrise_sunset = GetTimeOfSunriseSunset(
            verbose, override, use_geoclue, settings
        )
        if check_now != True:
            try:
                check(sunrise_sunset.times, settings)
            except Exception as e:
                print(f"check failed: {e}")

    except Exception as e:
        print(f"ERROR during run_once(): {e} ")
