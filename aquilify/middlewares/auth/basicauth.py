import base64
from aquilify.wrappers import Request, Response
from typing import Optional, Dict, Any, Union

class BasicAuthBeforeStageHandler:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        environment: Optional[Dict[str, Any]] = None,
        protected_routes: Optional[Union[list, str]] = ["*"]
    ) -> None:
        self.username = None
        self.password = None
        self.unauthorized_message = "Unauthorized"
        self.auth_realm = 'Basic realm="Access to Aquilify"'
        self.protected_routes = protected_routes if isinstance(protected_routes, list) else [protected_routes]
        
        self._set_credentials(config, environment)
        
    def _set_credentials(self, config: Optional[Dict[str, Any]], environment: Optional[Dict[str, Any]]) -> None:
        if config:
            self.username = config.get("BASIC_AUTH_USERNAME")
            self.password = config.get("BASIC_AUTH_PASSWORD")
            self.unauthorized_message = config.get("UNAUTHORIZED_MESSAGE", "Unauthorized")
            self.auth_realm = config.get("AUTH_REALM", 'Basic realm="Access to Aquilify"')
        elif environment:
            self.username = environment.get("BASIC_AUTH_USERNAME")
            self.password = environment.get("BASIC_AUTH_PASSWORD")
            self.unauthorized_message = environment.get("UNAUTHORIZED_MESSAGE", "Unauthorized")
            self.auth_realm = environment.get("AUTH_REALM", 'Basic realm="Access to Aquilify"')

    @staticmethod
    def _extract_credentials(auth_header: str):
        auth_decoded = base64.b64decode(auth_header.split(' ')[1]).decode('utf-8')
        return tuple(auth_decoded.split(':', 1)) if ':' in auth_decoded else ('', '')

    async def __call__(self, request: Request) -> Response:
        request.scope['user'] = None
        if self._should_apply_middleware(request):
            try:
                auth_header = request.headers.get('Authorization')

                if not auth_header or not auth_header.startswith('Basic '):
                    raise ValueError("Invalid Authorization Header")

                provided_credentials = self._extract_credentials(auth_header)
                if not provided_credentials or provided_credentials != (self.username, self.password):
                    raise ValueError("Invalid Credentials")

                request.scope['user'] = self.username
            except Exception as e:
                request.scope['user'] = None
                return self._unauthorized_response()

    def _should_apply_middleware(self, request: Request) -> bool:
        route = request.url.path
        if "*" in self.protected_routes or route in self.protected_routes:
            return True
        return False

    def _unauthorized_response(self):
        response = Response(self.unauthorized_message, status_code=401)
        response.headers['WWW-Authenticate'] = self.auth_realm
        return response