import typing
import jinja2
import inspect

from os import PathLike
from enum import Enum

from typing import (
    Type,
    Optional, 
    List, 
    Callable, 
    Dict, 
    Union, 
    Any, 
    Sequence
)


from aquilify.wrappers import Request
from aquilify.settings.base import settings
from aquilify.template.jinja2 import Jinja2Template
from aquilify.utils.module_loading import import_string
from aquilify.exception.base import ImproperlyConfigured
from aquilify.template.xenarx.xenarx_template import XenarxTemplateResponse
from aquilify.settings.templates import TemplateConfigSettings


class AvailableTemplates(Enum):
    XENARX = "aquilify.template.xenarx.XenarxTemplate"
    JINJA2 = "aquilify.template.jinja2.Jinja2Template"

class TemplateConfig:
    def __init__(self, options: Dict[str, Any]):
        self.options = options

class TemplateBuilder:
    @staticmethod
    def get_template_backend() -> str:
        try:
            templates = getattr(settings, 'TEMPLATES', None)

            if not templates:
                raise ImproperlyConfigured("TEMPLATES settings not found")
            
            _config_settings = TemplateConfigSettings()
            _config_settings.fetch()
            _settings = _config_settings.template_data[0]

            return _settings.get('backend')

        except ImproperlyConfigured as e:
            raise ImproperlyConfigured(f"Error in get_template_backend: {e}")

    @staticmethod
    def validate_template_backend(backend: str) -> None:
        if backend not in AvailableTemplates._value2member_map_:
            raise ValueError(f"Template {backend} not supported by AQUILIFY!")

    @staticmethod
    def import_template_module(backend: str) -> Type:
        try:
            return import_string(backend)
        except ImportError as e:
            raise ImproperlyConfigured(f"Error importing template module {backend}: {e}")
        except Exception as e:
            raise ImproperlyConfigured(f"Error while importing template module: {e}")

    @staticmethod
    def build_template() -> Type:
        try:
            backend = TemplateBuilder.get_template_backend()
            TemplateBuilder.validate_template_backend(backend)
            return TemplateBuilder.import_template_module(backend)

        except (ImproperlyConfigured, ValueError) as e:
            raise ImproperlyConfigured(f"Error while building template: {e}")

class TemplateFactory:
    @staticmethod
    def create_template() -> Union[XenarxTemplateResponse, Jinja2Template]:
        template_cls = TemplateBuilder.build_template()

        config_settings = TemplateConfigSettings()
        config_settings.fetch()
        settings_data = config_settings.template_data[0]

        context_processors: List[Callable[[Request], Dict[str, Any]]] = settings_data['options'].get('context_processors') or []
        directory: Optional[Union[str, PathLike, Sequence[Union[str, PathLike]]]] = settings_data.get('dirs')
        extensions = settings_data['options'].get('extensions') or ()
        
        if inspect.getmodule(template_cls) == inspect.getmodule(XenarxTemplateResponse):
            template = XenarxTemplateResponse(
                context_processors = context_processors, 
                directory = directory, 
                extensions = extensions
            ) 
            
        elif inspect.getmodule(template_cls) == inspect.getmodule(Jinja2Template):
            env: typing.Optional["jinja2.Environment"] = settings_data['options'].get('enviroment') or None,
            autoscape =  settings_data['options'].get('autoscape') or True
            cache_size =  settings_data['options'].get('cache_size') or 400
            extensions = settings_data['options'].get('extensions') or ()
            
            template = Jinja2Template(
                context_processors = context_processors, 
                directory = directory,
                env = env,
                extensions = extensions,
                cache_size = cache_size,
                autoscape = autoscape
            )
            
        else:
            raise ImproperlyConfigured("Invalid template engine or not supported by AQUILIFY! %s" %(template_cls))

        return template
