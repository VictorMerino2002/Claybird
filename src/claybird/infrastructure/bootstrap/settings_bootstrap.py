import importlib.util
from pathlib import Path
from claybird.application.ports.outbound.dependency_container_port import DependencyContainerPort

class SettingsBootstrap:

    def __init__(self, container: DependencyContainerPort):
        self.container = container

    def load_settings(self, path: str) -> None:
        path_obj = Path(path)

        spec = importlib.util.spec_from_file_location(path_obj.stem, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Error loading settings from {path}")

        settings = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(settings)
        except Exception as e:
            raise RuntimeError(f"Error cargando settings desde {path}") from e

        self.container.register("settings", settings)