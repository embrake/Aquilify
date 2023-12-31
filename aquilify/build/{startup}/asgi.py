import os

from aquilify.core.asgi import (
    ASGI,
    Router
)

os.environ['AQUILIFY_SETTINGS_MODULE'] = "settings"

application = ASGI.application()

Router().finalize()
