import importlib
import os
import traceback
import warnings
import aquilify
from . import global_settings

from aquilify.utils.functional import LazyObject, empty

class ImproperlyConfigured(Exception):
    pass

ENVIRONMENT_VARIABLE = "AQUILIFY_SETTINGS_MODULE"

class SettingsReference(str):
    def __new__(self, value, setting_name):
        return str.__new__(self, value)
    def __init__(self, value, setting_name):
        self.setting_name = setting_name

class LazySettings(LazyObject):
    def _setup(self, name=None):
        settings_module = os.environ.get(ENVIRONMENT_VARIABLE)
        if not settings_module:
            desc = ("setting %s" % name) if name else "settings"
            raise ImproperlyConfigured(
                "Requested %s, but settings are not configured. "
                "You must either define the environment variable %s "
                "or call settings.configure() before accessing settings."
                % (desc, ENVIRONMENT_VARIABLE)
            )
        self._wrapped = Settings(settings_module)
    def __repr__(self):
        if self._wrapped is empty:
            return "<LazySettings [Unevaluated]>"
        return '<LazySettings "%(settings_module)s">' % {
            "settings_module": self._wrapped.SETTINGS_MODULE,
        }
    def __getattr__(self, name):
        if (_wrapped := self._wrapped) is empty:
            self._setup(name)
            _wrapped = self._wrapped
        val = getattr(_wrapped, name)
        if name == "SECRET_KEY" and not val:
            raise ImproperlyConfigured("The SECRET_KEY setting must not be empty.")
        self.__dict__[name] = val
        return val
    def __setattr__(self, name, value):
        if name == "_wrapped":
            self.__dict__.clear()
        else:
            self.__dict__.pop(name, None)
        super().__setattr__(name, value)
    def __delattr__(self, name):
        super().__delattr__(name)
        self.__dict__.pop(name, None)
    def configure(self, default_settings=global_settings, **options):
        if self._wrapped is not empty:
            raise RuntimeError("Settings already configured.")
        holder = UserSettingsHolder(default_settings)
        for name, value in options.items():
            if not name.isupper():
                raise TypeError("Setting %r must be uppercase." % name)
            setattr(holder, name, value)
        self._wrapped = holder
    @property
    def configured(self):
        return self._wrapped is not empty
    def _show_deprecation_warning(self, message, category):
        stack = traceback.extract_stack()
        filename, _, _, _ = stack[-4]
        if not filename.startswith(os.path.dirname(aquilify.__file__)):
            warnings.warn(message, category, stacklevel=2)

class Settings:
    def __init__(self, settings_module):
        for setting in dir(global_settings):
            if setting.isupper():
                setattr(self, setting, getattr(global_settings, setting))
        self.SETTINGS_MODULE = settings_module
        mod = importlib.import_module(self.SETTINGS_MODULE)
        tuple_settings = (
            "ALLOWED_HOSTS",
            "TEMPLATES",
            "SECRET_KEY_FALLBACKS",
        )
        self._explicit_settings = set()
        for setting in dir(mod):
            if setting.isupper():
                setting_value = getattr(mod, setting)
                if setting in tuple_settings and not isinstance(setting_value, (list, tuple)):
                    raise ImproperlyConfigured(
                        "The %s setting must be a list or a tuple." % setting
                    )
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)
                
    def is_overridden(self, setting):
        return setting in self._explicit_settings

    def __repr__(self):
        return '<%(cls)s "%(settings_module)s">' % {
            "cls": self.__class__.__name__,
            "settings_module": self.SETTINGS_MODULE,
        }

class UserSettingsHolder:

    SETTINGS_MODULE = None

    def __init__(self, default_settings):
        self.__dict__["_deleted"] = set()
        self.default_settings = default_settings

    def __getattr__(self, name):
        if not name.isupper() or name in self._deleted:
            raise AttributeError
        return getattr(self.default_settings, name)

    def __setattr__(self, name, value):
        self._deleted.discard(name)
        super().__setattr__(name, value)

    def __delattr__(self, name):
        self._deleted.add(name)
        if hasattr(self, name):
            super().__delattr__(name)

    def __dir__(self):
        return sorted(
            s
            for s in [*self.__dict__, *dir(self.default_settings)]
            if s not in self._deleted
        )

    def is_overridden(self, setting):
        deleted = setting in self._deleted
        set_locally = setting in self.__dict__
        set_on_default = getattr(
            self.default_settings, "is_overridden", lambda s: False
        )(setting)
        return deleted or set_locally or set_on_default

    def __repr__(self):
        return "<%(cls)s>" % {
            "cls": self.__class__.__name__,
        }


settings = LazySettings()
