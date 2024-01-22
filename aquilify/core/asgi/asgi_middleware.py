import importlib

class ASGIMiddlewareLoaderError(Exception):
    pass

class ASGIMiddlewareLoader:
    def __init__(self, settings_module='settings'):
        self.settings_module = settings_module
        
    def load_asgi_middlewares(self):
        try:
            settings = importlib.import_module(self.settings_module)
            asgi_middlewares = getattr(settings, 'ASGI_MIDDLEWARES', [])
            
            if not asgi_middlewares:
                pass

            if not isinstance(asgi_middlewares, list):
                raise ASGIMiddlewareLoaderError("Invalid ASGI_MIDDLEWARES configuration")

            middlewares = []

            for middleware_path in asgi_middlewares:
                module_name, object_name = middleware_path.rsplit('.', 1)
                middleware_module = importlib.import_module(module_name)
                middleware = getattr(middleware_module, object_name)
                middlewares.append(middleware)

            return middlewares

        except ImportError:
            raise ASGIMiddlewareLoaderError(f"Could not import {self.settings_module}.")
        except AttributeError:
            raise ASGIMiddlewareLoaderError(f"ASGI_MIDDLEWARES not found in {self.settings_module}.")
        except ASGIMiddlewareLoaderError as e:
            raise e
        except Exception as e:
            raise ASGIMiddlewareLoaderError(f"Error: {e}")
