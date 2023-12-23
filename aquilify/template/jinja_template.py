import typing
import warnings
from os import PathLike

from aquilify.wrappers import Request
from aquilify.responses import HTMLResponse

try:
    import jinja2
    if hasattr(jinja2, "pass_context"):
        pass_context = jinja2.pass_context
    else:  # pragma: nocover
        pass_context = jinja2.contextfunction  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: nocover
    jinja2 = None  # type: ignore[assignment]

from aquilify.settings.templates import TemplateConfigSettings

try:
    _config_settings = TemplateConfigSettings()
    _config_settings.fetch()
    _settings = _config_settings.template_data[0]
except Exception as e:
    raise Exception("Template settings not found in settings.py, configure it before you use.")

class _TemplateResponse(HTMLResponse):
    def __init__(
        self,
        template: typing.Any,
        context: typing.Dict[str, typing.Any],
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
        content_type: typing.Optional[str] = None
    ):
        self.template = template
        self.context = context
        content = template.render(context)
        super().__init__(content, status_code, headers, content_type)

class Jinja2Templates:
    """
    templates = Jinja2Templates("templates")

    return templates.TemplateResponse("index.html", {"request": request})
    """

    @typing.overload
    def __init__(
        self,
        directory: "typing.Union[str, PathLike[typing.AnyStr], typing.Sequence[typing.Union[str, PathLike[typing.AnyStr]]]]",  # noqa: E501
        *,
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = None,
        **env_options: typing.Any,
    ) -> None:
        ...

    @typing.overload
    def __init__(
        self,
        *,
        env: "jinja2.Environment",
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = None,
    ) -> None:
        ...

    def __init__(
        self,
        directory: "typing.Union[str, PathLike[typing.AnyStr], typing.Sequence[typing.Union[str, PathLike[typing.AnyStr]]], None]" = _settings.get('dirs') or None,  # noqa: E501
        *,
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = _settings['options'].get('context_processors') or None,
        env: typing.Optional["jinja2.Environment"] = _settings['options'].get('enviroment') or None,
        **env_options: typing.Any,
    ) -> None:
        if env_options:
            warnings.warn(
                "Extra environment options are deprecated. Use a preconfigured jinja2.Environment instead.",  # noqa: E501
                DeprecationWarning,
            )
        assert jinja2 is not None, "jinja2 must be installed to use Jinja2Templates"
        assert directory or env, "either 'directory' or 'env' arguments must be passed"
        assert _settings.get('backend') != 'aquilify.template.jinja2', "Aquilify currently support Jinj2 as template engine"
        self.context_processors = context_processors or []
        self.autoscape =  _settings['options'].get('autoscape') or True
        self.extensions =  _settings['options'].get('extensions') or ()
        self.cache_size =  _settings['options'].get('cache_size') or 400
        if directory is not None:
            self.env = self._create_env(directory, **env_options)
        elif env is not None:
            self.env = env

    def _create_env(
        self,
        directory: "typing.Union[str, PathLike[typing.AnyStr], typing.Sequence[typing.Union[str, PathLike[typing.AnyStr]]]]",  # noqa: E501
        **env_options: typing.Any,
    ) -> "jinja2.Environment":
        loader = jinja2.FileSystemLoader(directory)
        env_options.setdefault("loader", loader)
        env_options.setdefault("autoescape", self.autoscape)
        env_options.setdefault("extensions", self.extensions)
        env_options.setdefault("cache_size", self.cache_size)

        return jinja2.Environment(**env_options)

    def get_template(self, name: str) -> "jinja2.Template":
        return self.env.get_template(name)

    @typing.overload
    async def TemplateResponse(
        self,
        request: Request,
        name: str,
        context: typing.Optional[typing.Dict[str, typing.Any]] = None,
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
        content_type: typing.Optional[str] = None
    ) -> _TemplateResponse:
        ...

    @typing.overload
    async def TemplateResponse(
        self,
        name: str,
        context: typing.Optional[typing.Dict[str, typing.Any]] = None,
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
        content_type: typing.Optional[str] = None
    ) -> _TemplateResponse:
        ...

    async def TemplateResponse(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> _TemplateResponse:
        if args:
            if isinstance(
                args[0], str
            ):
                warnings.warn(
                    "The `name` is not the first parameter anymore. "
                    "The first parameter should be the `Request` instance.\n"
                    'Replace `TemplateResponse(name, {"request": request})` by `TemplateResponse(request, name)`.',  # noqa: E501
                    DeprecationWarning,
                )

                name = args[0]
                context = args[1] if len(args) > 1 else kwargs.get("context", {})
                status_code = (
                    args[2] if len(args) > 2 else kwargs.get("status_code", 200)
                )
                headers = args[2] if len(args) > 2 else kwargs.get("headers")
                content_type = args[3] if len(args) > 3 else kwargs.get("content_type")

                if "request" not in context:
                    raise ValueError('context must include a "request" key')
                request = context["request"]
            else:  # the first argument is a request instance (new style)
                request = args[0]
                name = args[1] if len(args) > 1 else kwargs["name"]
                context = args[2] if len(args) > 2 else kwargs.get("context", {})
                status_code = (
                    args[3] if len(args) > 3 else kwargs.get("status_code", 200)
                )
                headers = args[4] if len(args) > 4 else kwargs.get("headers")
                content_type = args[5] if len(args) > 5 else kwargs.get("content_type")
        else:  # all arguments are kwargs
            if "request" not in kwargs:
                warnings.warn(
                    "The `TemplateResponse` now requires the `request` argument.\n"
                    'Replace `TemplateResponse(name, {"context": context})` by `TemplateResponse(request, name)`.',  # noqa: E501
                    DeprecationWarning,
                )
                if "request" not in kwargs.get("context", {}):
                    raise ValueError('context must include a "request" key')

            context = kwargs.get("context", {})
            request = kwargs.get("request", context.get("request"))
            name = typing.cast(str, kwargs["name"])
            status_code = kwargs.get("status_code", 200)
            headers = kwargs.get("headers")
            content_type = kwargs.get("content_type")

        context.setdefault("request", request)
        for context_processor in self.context_processors:
            context.update(await context_processor(context, request))

        template = self.get_template(name)
        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            content_type=content_type,
        )
