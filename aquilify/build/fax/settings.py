SETTINGS = """############################################# AQUILIFY APP SETTINGS #############################################
import os
import pathlib 

"use development" # calling development server from aquilif.core.server @noql -> 5391 
# change it to "use production" in production usage.

BASE_DIR = pathlib.Path(__file__).resolve().parent

# Warning - Do not make changes to this ENTRY_POINT it may broke the whole application.
# For more info about ENTERY_POINT :: refer @noql -> `/__root__.py`

ENTRY_POINT = "__root__.__instance__"

ASGI_APPLICATION = "asgi.application"

SECRET_KEY = "%s" # replace with you own strong and secure secret key.
# A secret key for secure session data and other cryptographic operations. 
# Keep this key secret and unique for your application.

DEFAULT_CHARSET = 'UTF-8'

DEBUG = True # Disable the DEBUG mode in production usage, due to security measures.

STRICT_SLASHES = True # Strict slashes is not implemented yet, so use the regular method to add STRICT_SLASHES

METHODS_RANGE = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"] # # Methods Range is not implemented yet, so it uses the deafult configuration.

ROOT_ROUTING = "routing"

### Trusted Host Middleware Configuration...

ALLOWED_HOSTS = ["*"] # * indicate to allow all the hosts.

# Additional Configuration...

ALLOW_SUBDOMAINS = True
REDIRECT_ON_FAILS = False
REDIRECT_URL = ""
ENFORCE_HTTPS = False
WWW_REDIRECT = False

API_CONSOLE_URL = '/api/console'

STATIC_CHUNK_SIZE = 65536

STATIC_URL = '/static/'

STATIC_MULTI_URL = [ ] 

STATICFILE_DIRS = [
    os.path.join(BASE_DIR, 'static')
]

MEDIA_DIRS = [
    os.path.join(BASE_DIR, 'media'),
]

MEDIA_URL = "/media/"

### X-FRAME-OPTIONS Configuration...

# Replace the value according to your needs; it may conflict with the XFrameOptionsMiddleware.
# For more information, visit: http://aquilify.vvfin.in/middlewares/core/x-frame-options
# Refer to @noql -> 5369
# Learn more about security headers at: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options

X_FAME_OPTIONS = "SAMEORIGIN"

# APPLICATION_DISPATCHER has not been confiured yet so use the manual setting to configure it.

APPLICATION_DISPATCHER = [ ]

### Templates Configuration...

# For detailed configuration information, visit: http://aquilify.vvfin.in/template/jinja2/settings
# Additional details available at @noql -> 5370.

TEMPLATES = [
    {
        "BACKEND": "aquilify.template.jinja2",
        "DIRS": [ os.path.join(BASE_DIR, "templates") ],
        "CSRF": "aquilify.security.csrf.CSRF",
        "OPTIONS": {
            "autoscape": True,
            "context_processors": [
                "aquilify.template.context_processors.URLContextProcessor",
                "aquilify.template.context_processors.CSRFContextView",
                "aquilify.core.messages.context_processors.Messages",
                "aquilify.template.context_processors.RequestContext"
            ],
            "extensions": [
                "aquilify.template.extensions.URLConstructor"
            ]
        }
    }
]

# CSRF Configuration...

# visit :: http://aquilify.vvfin.in/security/csrf

CSRF = [
    {
        "BACKEND": "aquilify.security.csrf.CSRF",
        "OPTIONS": {
            "secret_key": SECRET_KEY,
            "ip_verification": True,
            "trusted_ips": ["*"],
            "protected_methods": ["POST", "PUT", "DELETE"],
            "cookie_options": {"httponly": True, "secure": True, "samesite": 'strict'}
        }
    }
]

# Middleware configuration...

# You can pass either a string or a dictionary. For example:
# MIDDLEWARE = [
#    "aquilify.middlewares.XFrameOptionsMiddleware", # String middleware with default configuration.
#    {
#        "origin": "aquilify.middlewares.GzipMiddleware",
#        "order": 1,
#        "condition": "Your condition",
#        "__init__": "app",
#        "other arguments..."
#    }
# ]

# At present, we exclusively support the current app instance. This functionality dynamically adds the app instance to your class '__init__'.
# For additional details, please visit: http://aquilify.vvfin.in/middlewares/core

# The core middleware offers numerous benefits but also comes with certain exceptions. Therefore, we highly recommend using middleware hooks.
# Unlike core middleware, middleware hooks have the capability to intercept both before and after the request,
# as well as before and after the response, without any exceptions. This means you can modify the request before serving it.

MIDDLEWARES = [
    "aquilify.middlewares.XFrameOptionsMiddleware",
    "aquilify.middlewares.GzipMiddleware",
    "aquilify.middlewares.StaticMiddleware",
    "aquilify.middlewares.TrustedhostMiddleware",
    "aquilify.middlewares.CSRFMiddleware",
    "aquilify.middlewares.MediaMiddleware",
    "aquilify.middlewares.ConditionalGetMiddleware",
    "aquilify.core.messages.middleware.MessageMiddleware",
]

# stage handlers are the middleware hooks with advance features and configurations...
# we highly recommend users to use the middleware hooks in place of using regular middleware.
# For more info visit :: http://aquilify.vvfin.in/middlewares/hooks

STAGE_HANDLERS = [
    { "origin": "aquilify.core.backend.sessions.InMemorySessionBeforeStage", "stage": "before"},
    { "origin": "aquilify.core.messages.middleware.MessageBeforeStage", "stage": "before" }
]

ASGI_MIDDLEWARES = [ ]

## Database Configuration..

DATABASE = {
    "default": {
        "ENGINE": "aquilify.orm.Sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "MODELS": [ ]
    }
}

### Sessions Configuration....

# SESSIONS_CONFIG is a list of dictionaries containing session configuration settings for Aquilify.

# Memory backend configuration:
# - "backend": "memory" specifies the memory backend for session storage.
#   Configuration includes:
#   - "secret_key": SECRET_KEY uses the SECRET_KEY variable for session encryption.
#   - "session_lifetime": 30 sets the session lifetime in minutes for the memory backend.

# For further details on session configurations, refer to Aquilify documentation.

SESSION_BACKEND = 'memory'
SESSION_SECRET_KEY = SECRET_KEY

SESSION_MAX_AGE = 1800
SESSION_LIFETIME = 30
SESSION_SECURE = True
SESSION_HTTPONLY = True
SESSION_SAMESITE = "Lax"

SESSION_COOKIE_DOMAIN = 'localhost'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False

SESSION_COOKIE_SAMESITE = 'Lax'


SECRET_KEY_FALLBACKS = []

# LIFESPAN Handling...

LIFESPAN_EVENTS = [ ]

# GzipMiddleware Configuration

# GZIP_COMPRESSION_LEVEL: Set the Gzip compression level to 7 for optimal compression.

# GZIP_COMPRESSION_CONTENT_TYPES: List of content types that will undergo Gzip compression.
# Supported content types include:
# - 'text/html'
# - 'text/css'
# - 'application/javascript'
# - 'application/json'
# - 'image/svg+xml'
# - 'application/xml'

# GZIP_IGNORE_CONTENT_LENGHT: Specifies whether to ignore content length for Gzip compression.
# Set to False to consider content length.

# GZIP_CONTENT_ENCODING: Indicates the content encoding to be used, in this case, set to ["gzip"].

# GZIP_EXCLUDE_PATHS: List of paths to be excluded from Gzip compression.
# Currently empty [] - add paths to exclude from compression.

# GZIP_COMPRESSION_FUNCTION: Pass the path to a custom compression function.
# Example usage: {"compression.mycustomfunc"}
# This function can be utilized for specific compression requirements.

# Ensure these settings align with the optimization and compression needs of your application.

GZIP_COMPRESSION_LEVEL = 7
GZIP_COMPRESSION_CONTENT_TYPES = ['text/html','text/css','application/javascript','application/json', 'image/svg+xml', 'application/xml']
GZIP_IGNORE_CONTENT_LENGHT = False
GZIP_CONTENT_ENCODING = ["gzip"]
GZIP_EXCLUDE_PATHS = []
GZIP_COMPRESSION_FUNCTION = {} # pass the path to cutom compression function... e.g, {"compression.mycustomfunc"}

# SIGNING BACKEND

SIGNING_BACKEND = "aquilify.core.signing.TimestampSigner"


STORAGE_BACKEND = [
    {
        "static": [
            "aquilify.core.files.storage.FileSystemStorage"
        ]
    },
    {
        "sessions": {
            "memory": "aquilify.core.backend.sessions.storage.InMemorySessionStorage",
            "cookie": "aquilify.core.backend.sessions.storage.CookieSessionStorage"
        }
    }
]

MESSAGE_STORAGE = 'aquilify.core.messages.storage.fallback.FallbackStorage'

ENVIROMENT = {
    'lxenviroment': ['packlib'] # add all the .lxe file in this list
}
"""