import subprocess
from gi.repository import Gio, GLib
from typing import TypedDict, NotRequired, get_type_hints

default_config_file = ".var/gnome-night-shift/data.json"
SCHEMA_ID = "org.gnome.shell.extensions.night-shift"


def _compile_schema(schema_path, schema_id):
    try:
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_path, Gio.SettingsSchemaSource.get_default(), False
        )
        schema = schema_source.lookup(schema_id, True)
        if schema is None:
            raise LookupError(f"schema {schema_id} not found")

        return schema

    except Exception as e:
        import sys

        print(
            f"night-shift: settings unavailable, nothing will be saved ({e})",
            file=sys.stderr,
        )


class Store(TypedDict):
    day_or_night: str
    last_known_coordinates: tuple[float, float]
    static_latitude: str
    static_longitude: str
    timestamp: str
    times: tuple[str, str]
    tzid: str
    use_geoclue: bool


class DataStore:

    def __init__(self, schema_path):
        self.data: Store | None = None
        if schema_path == "DEFAULT":
            self.data_path = default_config_file
            self.schema = None
            self.data = None
        else:
            self.schema = _compile_schema(schema_path, SCHEMA_ID)
            self.data = Gio.Settings.new_full(self.schema, None, None)

    def get(self, key: str):
        annotations = get_type_hints(Store)

        norm_key = key.replace("-", "_")
        value = annotations.get(norm_key)()

        match value:
            case bool():
                value = self.data[key]
                return value
            case str():
                value = self.data[key]
                return value
            case int():
                value = self.data[key]
                return value
            case _:
                value = self.data[key]
                return value

    def set(self, key: str, value):
        match value:
            case bool():  # bool must go before int: bool is a subclass of int
                self.data.set_boolean(key, value)
            case str():
                self.data.set_string(key, value)
            case int():
                self.data.set_int(key, value)
            case GLib.Variant():  # tuples like "times" (ss) and coords (dd)
                self.data.set_value(key, value)
            case _:
                raise TypeError(
                    f"can't save {key}: unsupported type {type(value).__name__}"
                )

    @property
    def available(self) -> bool:
        return self.data is not None


if __name__ == "__main__":
    DataStore()
