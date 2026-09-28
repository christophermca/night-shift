import subprocess
from gi.repository import Gio
from typing import TypedDict, NotRequired, get_type_hints

# package_dir = Path(__file__).parent
# schema_dir = package_dir / "schemas"


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
        # settings = Gio.Settings(self.schema)
        annotations = get_type_hints(Store)

        undersc = key.replace("-", "_")
        value = annotations.get(undersc)
        match value():
            case str():
                value = self.data[key]
                return value
            case bool():
                value = self.data[key]
                return value
            case int():
                value = self.data[key]
                return value
            case _:
                value = self.data[key]
                return value

    def set(self, key: str, value):
        print("key_you", key, value)
        valueType = type(value)

        match valueType():
            case str():
                print(key)
                self.data.set_string(key, value)
            case bool():
                print(key)
                self.data.set_boolean(key, value)
            case int():
                print("int", key)
                self.data.set_int(key, value)
            case _:
                self.data.set_property(key, value)

    @property
    def available(self) -> bool:
        return self.data is not None


if __name__ == "__main__":
    DataStore()
