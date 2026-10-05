from pathlib import Path
from .services import Services
from .cli import setup_arguments

service_module_dir = Path(__file__).parent
source_units_dir = service_module_dir / "systemd" / "user"

target_dir = Path.home() / ".local" / "share" / "systemd" / "user"


class NightShiftServices(Services):
    def __init__(
        self,
        source_dir=source_units_dir,
        target_dir=target_dir,
        schema=None,
    ):
        self.schema_path = schema
        super().__init__(source_dir, target_dir)

    def setup(self, schema_path, build_only):
        return super().setup(schema_path, build_only)

    def start(self):
        super().start()

    def stop(self):
        super().stop()

    def destroy(self):
        super().destroy()
