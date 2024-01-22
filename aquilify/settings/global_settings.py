############################################# AQUILIFY APP SETTINGS #############################################
import os
import pathlib 

"use development" # calling development server from aquilif.core.server @noql -> 5391 
# change it to "use production" in production usage.

BASE_DIR = pathlib.Path(__file__).resolve().parent

# Warning - Do not make changes to this ENTRY_POINT it may broke the whole application.
# For more info about ENTERY_POINT :: refer @noql -> `/__root__.py`

ENTRY_POINT = "__root__.__instance__"

SECRET_KEY = "aquilify-insecure?V(_[i=`>0IRBe_W" # replace with you own strong and secure secret key.
# A secret key for secure session data and other cryptographic operations. 
# Keep this key secret and unique for your application.

DEBUG = True # Disable the DEBUG mode in production usage, due to security measures.
STRICT_SLASHES = True # Strict slashes is not implemented yet, so use the regular method to add STRICT_SLASHES
METHODS_RANGE = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH", "TRACE"] # # Methods Range is not implemented yet, so it uses the deafult configuration.

### Trusted Host Middleware Configuration...

ALLOWED_HOSTS = ["*"] # * indicate to allow all the hosts.

# Additional Configuration...

ALLOW_SUBDOMAINS = True
REDIRECT_ON_FAILS = False
REDIRECT_URL = ""
ENFORCE_HTTPS = False
WWW_REDIRECT = False

### X-FRAME-OPTIONS Configuration...

# Replace the value according to your needs; it may conflict with the XFrameOptionsMiddleware.
# For more information, visit: http://aquilify.vvfin.in/middlewares/core/x-frame-options
# Refer to @noql -> 5369
# Learn more about security headers at: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options

X_FAME_OPTIONS = "SAMEORIGIN"

# APPLICATION_DISPATCHER has not been confiured yet so use the manual setting to configure it.

APPLICATION_DISPATCHER = ["__root__", {"/myapp2": "app2.main.myapp2"}]

### Templates Configuration...

# For detailed configuration information, visit: http://aquilify.vvfin.in/template/jinja2/settings
# Additional details available at @noql -> 5370.

TEMPLATES = [
    {
        "BACKEND": "aquilify.template.jinja2",
        "DIRS": [ os.path.join(BASE_DIR, "templates"), os.path.join(BASE_DIR, "views") ],
        "CSRF": "aquilify.security.csrf.CSRF",
        "OPTIONS": {
            "autoscape": True,
            "context_processors": [
                "aquilify.template.context_processors.URLContextProcessor",
                "aquilify.template.context_processors.CSRFContextView"
            ],
            "extensions": [
                "aquilify.template.extensions.URLConstructor"
            ]
        }
    }
]

CSRF = [
    {
        "BACKEND": "aquilify.security.csrf.CSRF",
        "OPTIONS": {
            "secret_key": SECRET_KEY
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
    "aquilify.middlewares.MediaMiddleware"
]

# stage handlers are the middleware hooks with advance features and configurations...
# we highly recommend users to use the middleware hooks in place of using regular middleware.
# For more info visit :: http://aquilify.vvfin.in/middlewares/hooks

STAGE_HANDLERS = [
    { "origin": "aquilify.core.backend.sessions.InMemorySessionBeforeStage", "stage": "before"}
]

### Sessions Configuration....

# SESSIONS_CONFIG is a list of dictionaries containing session configuration settings for Aquilify.

# Memory backend configuration:
# - "backend": "memory" specifies the memory backend for session storage.
#   Configuration includes:
#   - "secret_key": SECRET_KEY uses the SECRET_KEY variable for session encryption.
#   - "session_lifetime": 30 sets the session lifetime in minutes for the memory backend.

# For further details on session configurations, refer to Aquilify documentation.

SESSIONS_CONFIG = [
    {
        "backend": "memory",
        "secret_key": SECRET_KEY,
        "session_lifetime": 30
    }
]

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

# Static Middleware Configuration (Uncomment in case of use)

# STATIC_CONFIG: Specifies the mapping of URL paths to the respective static file directories.
# Example: '/static/': os.path.join(BASE_DIR, 'static') maps '/static/' URL requests to the 'static' directory.

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

STORAGE_BACKEND = [
    {
        "static": [
            "aquilify.core.files.static.storage"
        ]
    }
]

ENVIROMENT = {
    'lxenviroment': ['packlib'] # add all the .lxe file in this list
}
