from typing import  Optional
from ..wrappers import Request, Response
import importlib
import logging

logger = logging.getLogger(__name__)

class XFrameOptionsMiddleware:
    ALLOW_DENY_OPTIONS = ["DENY", "SAMEORIGIN"]

    @staticmethod
    def get_allow_from(settings_module: str = 'settings') -> Optional[str]:
        allow_from = None
        try:
            settings = importlib.import_module(settings_module)
            allow_from = getattr(settings, 'X_FAME_OPTIONS', "SAMEORIGIN")
            if allow_from.upper() not in XFrameOptionsMiddleware.ALLOW_DENY_OPTIONS:
                raise ValueError("Invalid 'allow_from' value. Choose from 'DENY' or 'SAMEORIGIN'")
        except ImportError as ie:
            logger.error(f"Settings module '{settings_module}' not found: {ie}")
            raise ImportError(f"Settings module '{settings_module}' not found: {ie}")
        except AttributeError as ae:
            logger.error(f"Attribute 'X_FAME_OPTIONS' not found in '{settings_module}': {ae}")
            raise AttributeError(f"Attribute 'X_FAME_OPTIONS' not found in '{settings_module}': {ae}")
        except ValueError as ve:
            logger.error(str(ve))
            raise ValueError(str(ve))
        except Exception as e:
            logger.error(f"Error fetching 'allow_from' from settings: {e}")
            raise Exception(f"Error fetching 'allow_from' from settings: {e}")
        return allow_from

    async def __call__(self, request: Request, response: Response) -> Response:
        allow_from = self.get_allow_from()
        if allow_from is not None:
            if not 'X-Frame-Options' in response.headers:
                response.headers["X-Frame-Options"] = allow_from
        return response
