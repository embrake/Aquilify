import importlib.util

class DispatcherConfigSettings:
    def __init__(self, settings_module_path="./settings.py") -> None:
        self.settings_module_path = settings_module_path
        self.dispatcher_instances = {}

    def fetch_dispatcher_config(self):
        try:
            settings = self._load_settings_module()
            dispatcher_config = getattr(settings, "APPLICATION_DISPATCHER", None)

            if dispatcher_config and len(dispatcher_config) == 2:
                root_instance, instance_dict = dispatcher_config

                if isinstance(root_instance, str) and isinstance(instance_dict, dict):
                    for key, value in instance_dict.items():
                        module = self._import_module(root_instance)
                        instance = self._get_instance_from_path(module, value)
                        if instance:
                            self.dispatcher_instances[key] = instance

        except (FileNotFoundError, AttributeError, ImportError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def _import_module(self, module_name):
        return importlib.import_module(module_name)

    def _get_instance_from_path(self, module, instance_path):
        return getattr(module, instance_path) if instance_path else None
