ASGI = """import os

from aquilify.core.asgi import (
    ASGI,
    Router
)

from aquilify.core import Aquilify

os.environ['AQUILIFY_SETTINGS_MODULE'] = "settings"

# Warning: Do not modify this file or rename the variables.
# Making any changes could potentially break the application and cause malfunctions.

# The 'application' variable declares the current ASGI (Asynchronous Server Gateway Interface) application.
# This application originates from the '__root__' directory of this project.

application: Aquilify = ASGI.application()

# The Router.finalize() method checks all the routes and schematic instances
# to ensure they are properly configured before finalizing the route to the web.

Router().finalize()
"""