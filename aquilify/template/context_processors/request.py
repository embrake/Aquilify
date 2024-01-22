from typing import Any, Dict


class RequestContext:
    
    async def __call__(self, context: Dict[str, str], request) -> Any:
        context['request'] = request
        return context