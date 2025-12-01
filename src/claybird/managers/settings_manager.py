import importlib.util

class SettingsManager:

    settings_path = "settings.py"

    @classmethod
    def set_settings_path(cls, path):
        cls.settings_path = path

    @classmethod
    def get_settings(cls):
        spec = importlib.util.spec_from_file_location("settings", cls.settings_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings