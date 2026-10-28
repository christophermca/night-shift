import argparse
from unittest.mock import patch

import pytest

from night_shift_services.cli import register


@pytest.fixture
def services_class():
    # run() does `from . import NightShiftServices`, so patch it on the package
    with patch("night_shift_services.NightShiftServices") as services_class:
        yield services_class


def run_services(*args):
    """Parse like night-shift does, then call the handler register() returned."""
    parser = argparse.ArgumentParser(prog="night-shift")
    handler = register(parser.add_subparsers(dest="command"))
    return handler(parser.parse_args(["services", *args]))


def test_setup_builds_units_for_the_schema(services_class):
    run_services("setup", "/path/to/schemas", "--build-only")

    services_class.assert_called_once_with()
    services_class.return_value.setup.assert_called_once_with(
        "/path/to/schemas", True
    )


@pytest.mark.parametrize(
    "subcommand, method",
    [("start", "start"), ("stop", "stop"), ("taredown", "destroy")],
)
def test_subcommands(services_class, subcommand, method):
    run_services(subcommand)

    getattr(services_class.return_value, method).assert_called_once_with()
