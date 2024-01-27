from typing import Callable, Dict, Any
from os import PathLike

from aquilify.template.xenarx import loaders
from aquilify.responses import HTMLResponse
from aquilify.wrappers import Request
from aquilify.template.xenarx.enviroment import Environment

import aquilify.template.xenarx as xenarx

import typing
import warnings

class _BaseTemplateResponse(HTMLResponse):
    def __init__(
        self, 
        content: str | bytes | Callable[..., Any] | None = None, 
        status: int | None = 200, 
        headers: Dict[str, str | int] | None = None,
    ) -> None:
        super().__init__(content, status, headers)
        
    def __str__(self):
        return self.content
    
    def __repr__(self) -> str:
        return "BaseTemplateResponse(template = %s)" % ("xenarx Template | AQUILIFY")

class XenarxTemplateResponse:
    
    """
    templates = XenarxTemplateResponse("templates")

    return templates.render("index.html", {"request": request})
    """
    
    @typing.overload
    def __init__(
        self,
        directory: "typing.Union[str, PathLike[typing.AnyStr], typing.Sequence[typing.Union[str, PathLike[typing.AnyStr]]]]",  # noqa: E501
        *,
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = None,
        extensions: typing.Sequence[str | type["xenarx.node.Node"]] = (),
    ) -> None:
        ...
        
    @typing.overload
    def __init__(
        self,
        *,
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = None,
        extensions: typing.Sequence[str | type["xenarx.ext.Extension"]] = ()
    ) -> None:
        ...
    
    def __init__(
        self,
        directory: "typing.Union[str, PathLike[typing.AnyStr], typing.Sequence[typing.Union[str, PathLike[typing.AnyStr]]], None]" = None,  # noqa: E501
        *,
        context_processors: typing.Optional[
            typing.List[typing.Callable[[Request], typing.Dict[str, typing.Any]]]
        ] = None,
        extensions: typing.Sequence[str | type["xenarx.node.Node"]] = ()
    ) -> None:
        self.context_processors = context_processors
        self.template_dirs = directory
        self.extensions = extensions
        
    def _get_processor_name(
        self, 
        processor: typing.Optional[typing.Dict[str, typing.Any]]
    ) -> str:
        
        if hasattr(processor, '__call__'):
            if isinstance(processor, type):
                return f"Callable class '{processor.__name__}'"
            else:
                return f"Instance of callable class '{processor.__class__.__name__}'"
        else:
            return f"Function '{processor.__name__}'"

    async def _run_context_processors(
        self, 
        context: typing.Optional[typing.Dict[str, typing.Any]], 
        request: Request
    ) -> typing.Optional[typing.Dict[str, typing.Any]]:
        
        for processor in self.context_processors:
            processor_name = self._get_processor_name(processor)

            processed_context = await processor(context, request)
            if not isinstance(processed_context, dict):
                raise ValueError(f"{processor_name} must return a dictionary.")
            context = processed_context
        return context
    
    @typing.overload
    async def render(
        self,
        request: Request,
        name: str,
        context: typing.Optional[typing.Dict[str, typing.Any]] = None,
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None
    ) -> _BaseTemplateResponse:
        ...
        
    @typing.overload
    async def render(
        self,
        name: str,
        context: typing.Optional[typing.Dict[str, typing.Any]] = None,
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None
    ) -> _BaseTemplateResponse:
        ...
        
    async def render(
        self, *args: typing.Any, **kwargs: typing.Any
    ) -> _BaseTemplateResponse:
        
        env = Environment(extensions = self.extensions)
        env._build_extension()
        
        if args:
            if isinstance(
                args[0], str
            ):
                warnings.warn(
                    "The `name` is not the first parameter anymore. "
                    "The first parameter should be the `Request` instance.\n"
                    'Replace `render(name, {"request": request})` by `render(request, name)`.',  # noqa: E501
                    DeprecationWarning,
                )

                name = args[0]
                context = args[1] if len(args) > 1 else kwargs.get("context", {})
                status_code = (
                    args[2] if len(args) > 2 else kwargs.get("status_code", 200)
                )
                headers = args[2] if len(args) > 2 else kwargs.get("headers")

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
        else:  # all arguments are kwargs
            if "request" not in kwargs:
                warnings.warn(
                    "The `render` now requires the `request` argument.\n"
                    'Replace `render(name, {"context": context})` by `render(request, name)`.',  # noqa: E501
                    DeprecationWarning,
                )
                if "request" not in kwargs.get("context", {}):
                    raise ValueError('context must include a "request" key')

            context = kwargs.get("context", {})
            request = kwargs.get("request", context.get("request"))
            name = typing.cast(str, kwargs["name"])
            status_code = kwargs.get("status_code", 200)
            headers = kwargs.get("headers")

        context.setdefault("request", request)
        context: typing.Optional[typing.Dict[str, typing.Any]] = await self._run_context_processors(context, request)

        loader = xenarx.loader = loaders.FileReloader(self.template_dirs)
        template = loader(name)
        
        _template = template.render(
            {
                "request": request,
                **(context or {})
            }
        )
        
        return _BaseTemplateResponse(
            _template,
            status=status_code,
            headers=headers
        )