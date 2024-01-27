import importlib.util

class TemplateConfigSettings:
    def __init__(self, settings_module_path: str = "./settings.py") -> None:
        self.settings_module_path = settings_module_path
        self.template_data = []

    def fetch(self) -> None:
        try:
            with open(self.settings_module_path) as file:
                settings = self._load_settings_module()
                templates = getattr(settings, 'TEMPLATES', [])
                csrf = getattr(settings, 'CSRF', None)  # Fetch CSRF setting
                self._extract_templates(templates, csrf)

        except (FileNotFoundError, AttributeError, ValueError) as e:
            raise ImportError(f"Error loading settings.py: {e}")

    def _load_settings_module(self):
        spec = importlib.util.spec_from_file_location("settings", self.settings_module_path)
        settings = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(settings)
        return settings

    def _extract_templates(self, templates: list, csrf_setting) -> None:
        for template in templates:
            extracted_data = self._extract_template_data(template, csrf_setting)
            self.template_data.append(extracted_data)

    def _extract_template_data(self, template: dict, csrf_setting) -> dict:
        backend = self._get_backend(template)
        dirs = self._get_dirs(template)
        options = self._get_options(template)
        context_processors = self._load_context_processors(options.get('context_processors', []))
        extensions = self._load_extensions(options.get('extensions', []))
        csrf = self._load_csrf(template.get('CSRF', None))

        if csrf_setting is None and csrf is not None:
            raise ValueError("CSRF setting cannot be used before setting it up in settings.py")

        return {
            'backend': backend,
            'dirs': dirs,
            'csrf': csrf,
            'options': {
                'context_processors': context_processors,
                'enviroment': options.get('enviroment', None),
                'extensions': extensions,
                'cache_size': options.get('cache_size', 400)
            }
        }

    def _get_backend(self, template: dict) -> str:
        backend = template.get('BACKEND')
        return backend if backend else ""

    def _get_dirs(self, template: dict) -> list:
        dirs = template.get('DIRS', [])
        return dirs if isinstance(dirs, list) else [dirs] if dirs else []

    def _get_options(self, template: dict) -> dict:
        return template.get('OPTIONS', {})

    def _load_context_processors(self, processor_paths: list) -> list:
        processors = []
        for processor_path in processor_paths:
            processor = self._load_processor(processor_path)
            if processor:
                processors.append(processor)
        return processors
    
    def _load_extensions(self, processor_paths: list) -> list:
        processors = []
        for processor_path in processor_paths:
            processor = self._load_extenstions_processor(processor_path)
            if processor:
                processors.append(processor)
        return processors
    
    def _load_extenstions_processor(self, processor_path: str):
        if processor_path:
            try:
                parts = processor_path.split('.')
                module_path = '.'.join(parts[:-1])
                callback_name = parts[-1]
                callback_module = importlib.import_module(module_path)
                callback_obj = getattr(callback_module, callback_name)
                return callback_obj
            except (AttributeError, ImportError, ValueError) as e:
                print(f"Error fetching callback: {e}")
        return None

    def _load_processor(self, processor_path: str):
        if processor_path:
            try:
                parts = processor_path.split('.')
                module_path = '.'.join(parts[:-1])
                callback_name = parts[-1]
                callback_module = importlib.import_module(module_path)
                callback_obj = getattr(callback_module, callback_name)
                if isinstance(callback_obj, type):
                    callback_obj = callback_obj()
                return callback_obj
            except (AttributeError, ImportError, ValueError) as e:
                print(f"Error fetching callback: {e}")
        return None

    def _load_csrf(self, csrf_string: str):
        if csrf_string:
            return self._load_processor(csrf_string)
        return csrf_string
