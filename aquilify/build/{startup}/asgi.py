import os

from aquilify.core.asgi import (
    ASGI,
    Router
)

app = ASGI.application()

os.environ['AQUILIFY_SETTINGS_MODULE'] = "settings"

Router().finalize()
