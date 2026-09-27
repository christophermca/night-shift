import pytest

from unittest.mock import patch, MagicMock
from gnome_night_shift.bin.is_day_or_night import is_day_or_night


@pytest.fixture()
def mock_settings():
    """Mock Gio.Settings object"""
    settings = MagicMock()
    settings.get_value.return_value = ["06:00", "18:30"]  # sunrise, sunset
    return settings


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_day(mock_settings_func, mock_settings):
    """Test detection of daytime"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunrise(mock_settings_func, mock_settings):
    """Test detection night before sunrise"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "05:59"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunrise(mock_settings_func, mock_settings):
    """Test detection transition at sunrise"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "06:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_before_sunset(mock_settings_func, mock_settings):
    """Test detection of daytime before sunset"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:29"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "day")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_at_sunset(mock_settings_func, mock_settings):
    """Test detection of transition at sunset"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "18:30"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_is_day_or_night_during_night(mock_settings_func, mock_settings):
    """Test detection of nighttime"""
    mock_settings_func.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20:00"

        is_day_or_night()

        mock_settings.set_string.assert_called_with("day-or-night", "night")


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_no_settings_prints_instead_of_crashing(mock_settings_class, capsys):
    mock_settings_class.return_value.return_value = None

    assert is_day_or_night() is None

    assert "unable to check day or night" in capsys.readouterr().err


@pytest.mark.parametrize(
    "now, expected", [("05:59", "night"), ("12:00", "day"), ("18:30", "night")]
)
@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_given_times_are_used_instead_of_saved_ones(
    mock_settings_class, mock_settings, now, expected
):
    mock_settings_class.return_value.return_value = mock_settings

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = now

        result = is_day_or_night(("06:00", "18:30"))

    mock_settings.get_value.assert_not_called()
    mock_settings.set_string.assert_called_once_with("day-or-night", expected)
    assert result == expected


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_given_times_work_without_settings(mock_settings_class, capsys):
    mock_settings_class.return_value.return_value = None

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        result = is_day_or_night(("06:00", "18:30"))

    assert result == "day"
    captured = capsys.readouterr()
    assert "daytime" in captured.out
    assert "unable to save day-or-night" in captured.err


@patch("gnome_night_shift.bin.is_day_or_night.Settings")
def test_uses_the_settings_it_is_given(mock_settings_class, mock_settings):
    shared = MagicMock(return_value=mock_settings)  # a Settings(): call -> Gio

    with patch(
        "gnome_night_shift.bin.is_day_or_night.datetime"
    ) as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "12:00"

        is_day_or_night(("06:00", "18:30"), shared)

    mock_settings_class.assert_not_called()  # didn't build a second one
    mock_settings.set_string.assert_called_once_with("day-or-night", "day")
