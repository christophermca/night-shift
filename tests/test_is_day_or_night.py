import datetime
import pytest

from freezegun import freeze_time
from unittest.mock import patch, MagicMock, create_autospec
from gnome_night_shift.bin.settings import Settings
from gnome_night_shift.bin.is_day_or_night import is_day_or_night


@pytest.fixture(autouse=True)
def settings_class():
    """main() builds one Settings per run; fake it so no test touches GSettings."""
    with patch("gnome_night_shift.cli.Settings") as settings_class:
        yield settings_class


@freeze_time("12:00")
def test_is_day_or_night_during_day(settings_class):
    """Test detection of daytime"""
    TIMES = ("07:00", "20:00")

    result = is_day_or_night(TIMES, settings_class)

    assert result == "day"


@freeze_time("06:59")
def test_is_day_or_night_before_sunrise(settings_class):
    """Test detection night before sunrise"""
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings_class)

    assert result == "night"


@freeze_time("07:00")
def test_is_day_or_night_at_sunrise():
    """Test detection transition at sunrise"""
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings_class)
    assert result == "day"


@freeze_time("19:48")
def test_is_day_or_night_before_sunset():
    """Test detection of daytime before sunset"""
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings_class)
    assert result == "day"


@freeze_time("20:00")
def test_is_day_or_night_at_sunset():
    """Test detection of transition at sunset"""
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings_class)
    assert result == "night"


@freeze_time("20:01")
def test_is_day_or_night_during_night():
    """Test detection of nighttime"""
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings_class)
    assert result == "night"


# @pytest.mark.parametrize(
#     "now, expected", [("05:59", "night"), ("12:00", "day"), ("18:30", "night")]
# )
def test_given_times_are_used_instead_of_saved_ones():
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, None)
    assert result == "night"


def test_given_times_work_without_settings():
    TIMES = ("07:00", "20:00")
    result = is_day_or_night(TIMES, None)
    assert result == "night"


@freeze_time("14:00")
def test_uses_the_settings_it_is_given_in_day(settings_class):
    TIMES = None
    settings = create_autospec(Settings, instance=True)
    settings.get.return_value = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings)
    assert result == "day"


@freeze_time("21:00")
def test_uses_the_settings_it_is_given_at_night(settings_class):
    TIMES = None
    settings = create_autospec(Settings, instance=True)
    settings.get.return_value = ("07:00", "20:00")
    result = is_day_or_night(TIMES, settings)
    assert result == "night"
