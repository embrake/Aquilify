import importlib

class LifespanConfigError(Exception):
    pass

class ASGILifespanLoader:
    def __init__(self, settings_module='settings'):
        self.settings_module = settings_module
        
    def load_asgi_lifespans(self):
        try:
            settings = importlib.import_module(self.settings_module)
            asgi_lifespans = getattr(settings, 'LIFESPAN_EVENTS', [])
            
            if not asgi_lifespans:
                pass

            if not isinstance(asgi_lifespans, list):
                raise LifespanConfigError("Invalid LIFESPAN_EVENTS configuration")

            lifespans = []

            for lifespans_data in asgi_lifespans:
                module_name, object_name = lifespans_data.get('origin').rsplit('.', 1)
                middleware_module = importlib.import_module(module_name)
                middleware = getattr(middleware_module, object_name)
                if isinstance(middleware, type):
                        middleware = middleware()
                else:
                    middleware
                lifespans.append({'event': lifespans_data.get('event'), 'origin': middleware})

            return lifespans

        except ImportError:
            raise LifespanConfigError(f"Could not import {self.settings_module}.")
        except AttributeError:
            raise LifespanConfigError(f"LIFESPAN_EVENTS not found in {self.settings_module}.")
        except LifespanConfigError as e:
            raise e
        except Exception as e:
            raise LifespanConfigError(f"Error: {e}")