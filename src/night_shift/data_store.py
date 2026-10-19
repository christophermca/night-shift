import sys
import subprocess
from gi.repository import Gio, GLib
from typing import TypedDict, NotRequired, get_type_hints

default_config_file = ".var/night-shift/data.json"
DEFAULT_SCHEMA_ID = "com.github.christophermca.night-shift"


def _compile_schema(schema_path, schema_id) -> Gio.SettingsSchema | None:
    try:
        print("here")
        schema_source = Gio.SettingsSchemaSource.new_from_directory(
            schema_path, Gio.SettingsSchemaSource.get_default(), False
        )
        schema = schema_source.lookup(schema_id, True)
        if schema is None:
            raise LookupError(f"schema {schema_id} not found")

        return schema

    except Exception as e:
        print(
            f"night-shift: settings unavailable, nothing will be saved ({e})",
            file=sys.stderr,
        )


class TypedStore(TypedDict):
    day_or_night: str
    last_known_coordinates: tuple[float, float]
    static_latitude: str
    static_longitude: str
    timestamp: str
    times: tuple[str, str]
    tzid: str
    use_geoclue: bool


class DataStore:

    def __init__(self, schema_path: str):
        self.data: GObject | TypedStore | None = None
        self.schema: Gio.SettingsSchema | None = None
        self.schema_path = schema_path

        try:
            print("findme", self.schema_path)
            SCHEMA_XML = (Path(night_shift.__file__).parent / "schemas").glob(
                "*.gschema.xml"
            )
            print("HERE", SCHEMA_XML)
            package_id = schema_path.name.removesuffix(".gschema.xml")
            self.schema = _compile_schema(schema_path, schema_id=package_id)
            print(f"pkg_id{package_id}, self.schema: {self.schema}")

            if self.schema is not None:
                self.data = Gio.Settings.new_full(self.schema, None, None)
            else:
                self.data = None

        except Exception as e:
            print(
                f"night-shift: settings unavailable, nothing will be saved ({e})",
                file=sys.stderr,
            )
            self.data = None

    def get_keys(self) -> list[str]:
        if self.schema is None:
            return []
        else:
            return sorted(self.schema.list_keys())

    def get(self, key: str):
        if self.data is None:
            return None

        annotations = get_type_hints(TypedStore)

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
        if self.data is None:
            raise AttributeError("`data` is None")
            return None

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
