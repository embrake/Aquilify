############################################# AQUILIFY APP SETTINGS #############################################
import os

"use development" # calling development server from aquilif.core.server @noql -> 5391 
# change it to "use production" in production usage.

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Warning - Do not make changes to this ENTRY_POINT it may broke the whole application.
# For more info about ENTERY_POINT :: refer @noql -> `/__root__.py`

ENTRY_POINT = "__root__.__instance__"

SECRET_KEY = "?i\<<dO=|p`>2WbJ2Rs+BI@@B2}Dh+i>7qKifwekb.:_xrRn|V(_[i=`>0IRBe_W" # replace with you own strong and secure secret key.
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

# TEMPLATES variable contains a list of dictionaries specifying Aquilify template settings.
# - BACKEND: ["jinja2"] specifies the Jinja2 backend used by Aquilify.
# - DIRS: [ os.path.join(BASE_DIR, "templates") ] defines the directory where templates are located.

# Aquilify CSRF configuration:
# - CSRF: "aquilify.security.CSRF" specifies the CSRF security measures utilized by Aquilify.

# Aquilify template options:
# - OPTIONS contains various configurations:
#   - autoscape: True enables automatic HTML escaping to prevent vulnerabilities.
#   - cache_size: 128 specifies the cache size for template caching.
#   - extensions: [] lists any extensions used; currently empty.
#   - enable_template_cache: True activates template caching for improved performance.
#   - filters: {} dict any filter used; currently empty.
#   - globals: {} dict any globals variable used; currently empty.

# Context Processors:
# - context_processors includes the following:
#   - "aquilify.template.context_processors.url_builder.TemplateURLBuilder" for enhanced URL building.

# For detailed configuration information, visit: http://aquilify.vvfin.in/template/jinja2/settings
# Additional details available at @noql -> 5370.

TEMPLATES = [
    {
        "BACKEND": ["jinja2"],
        "DIRS": [ os.path.join(BASE_DIR, "templates") ],
        "OPTIONS": {
            "autoscape": True,
            "context_processors": [
                "aquilify.template.context_processors.url_builder.TemplateURLBuilder"
            ]
        }
    }
]

### Schematic Configuration...
# schematic @noql -> 5321

# Do not make changes to the default configuration, it may broke the schematic routing.
# For further help visit :: http://aquilify.vvfin.in/routing/schematic/configuration
# For further discussion visit @embrake/aquilify on Github at https://github.com/embrake/aquilify

# Schematic is a dynamic routing for Aquilify and it still under developement but you can freely use it in prodiction usage.
# Warnings @noql -> 5319

# - Schematic doesn't support dynamic middleware support, but still you can configure it by using the regular middlewares configurations.
# - Schematic requires instance class you may need to configure it manually.
# - Schematic doesn't suppot ROUTING PATTER so igonore to use the aquilify.schematic.routing (rule & websocket).

SCHEMATIC_APP_INSTANCE = [
    {
        "@": "aquilify.schematic.routing",
        "@rule": "aquilify.schematic.routing.rule",
        "@websocket": "aquilify.schematic.routing.websocket"
    }
]

# Database engine, Electrus in this case. You can change it based on your database choice,
# currently aquilify supports only ['Electrus'] database.

DATABASES = {
    'default': {
        'ENGINE': 'Electrus',
        'HOST': 'localhost',
        'PORT': 37017,
        'USER': 'root',
        'PASSWORD': 'root'
    }
}

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
    "aquilify.middlewares.CSPMiddleware",
    "aquilify.middlewares.StaticMiddleware",
    "aquilify.middlewares.TrustedhostMiddleware",
]

# stage handlers are the middleware hooks with advance features and configurations...
# we highly recommend users to use the middleware hooks in place of using regular middleware.
# For more info visit :: http://aquilify.vvfin.in/middlewares/hooks

STAGE_HANDLERS = [
    { "origin": "aquilify.backend.sessions.InMemorySessionBeforeStage", "stage": "before"}
]

### Sessions Configuration....
# Either use the variable configuration or SESSION_CONFIG,

# SESSION_BACKEND = "cookie"
# SESSION_SECRET_KEY = "mysecretkey"
# SESSION_MAX_AGE = 3600
# SESSION_LIFETIME = 30
# SESSION_SECURE = True
# SESSION_HTTPONLY = True
# SESSION_SAMESITE = "Lax"
# SESSION_COOKIE_NAME = "_session_id" 

# SESSIONS_CONFIG is a list of dictionaries containing session configuration settings for Aquilify.

# Default memory backend configuration:
# - "backend": "cookie" specifies the memory backend. Modify this based on your requirements.
#   Configuration options include:
#   - "secret_key": "mysecretkey" defines the secret key used for session encryption.
#   - "max_age": 3600 sets the maximum session age in seconds (currently commented out).
#   - "session_lifetime": 30 sets the session lifetime in minutes.
#   - "secure": True ensures sessions are transmitted over secure connections (HTTPS).
#   - "httponly": True restricts cookie access to HTTP requests only.
#   - "samesite": "Strict" prevents cross-site request forgery.
#   - "cookie_name": "_sessionid" names the session cookie.

# Memory backend configuration:
# - "backend": "memory" specifies the memory backend for session storage.
#   Configuration includes:
#   - "secret_key": SECRET_KEY uses the SECRET_KEY variable for session encryption.
#   - "session_lifetime": 30 sets the session lifetime in minutes for the memory backend.

# Note: The commented-out configuration provides an example of the cookie backend setup.
# For further details on session configurations, refer to Aquilify documentation.


SESSIONS_CONFIG = [
# Default config for memory `backend` change it by according to your requirements.
#    {
#        "backend": "cookie",
#        "secret_key": "mysecretkey",
#        "max_age": 3600,
#        "session_lifetime": 30,
#        "secure": True,
#        "httponly": True,
#        "samesite": "Strict",
#        "cookie_name": "_sessionid"
#    },
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

# STATIC_GZIP_COMPRESSION: Enable/disable Gzip compression for static files.
# Set to True to apply Gzip compression to static files.

# STATIC_MAX_AGE: Set the maximum age (in seconds) for caching static files in clients' browsers.
# Example: 3600 seconds (1 hour) sets the cache control max age to one hour.

# STATIC_RESPONSE_HANDLER: Define a custom response handler function for static files if needed.
# Currently set to None. Assign a custom function if required.

# STATIC_CHUNK_SIZE: Specifies the chunk size (in bytes) for static file transfer.
# Example: 65536 bytes (64 KB) sets the chunk size for data transfer.

# Uncomment and configure these settings based on your application's static file handling needs.

STATIC_CONFIG = { '/static/': os.path.join(BASE_DIR, 'static') }
STATIC_GZIP_COMPRESSION = True
STATIC_MAX_AGE = 3600
STATIC_RESPONSE_HANDLER = None
STATIC_CHUNK_SIZE = 65536

# CSP -> Content-Security-Policy Configuration

# Note: Aquilify prefers enabling the CSP Policy by default. If you are not familiar with CSP, remove the CSP middleware from the MIDDLEWARE [].
# Configure the settings as per your specific requirements. The following are default configurations.

# Base Configuration...

# CSP_DIRECTIVES: Contains directives specifying allowed sources for various resources.
# - 'default-src': ["'self'"] allows resources to be fetched from the same origin.
# - 'style-src': ["'self'", "'unsafe-inline'"] permits inline styles from the same origin and inline CSS.
# You may modify these directives based on your security policies.

# CSP_REPORT_URI: Specifies the URI where CSP violation reports will be sent (currently empty).
# CSP_REPORT_ONLY: If True, the browser only reports violations without enforcing the policy.

# Additional Configuration...

# Additional security-related configurations:
# - CSP_NONCE_LENGTH: Defines the length of nonce values used in CSP.
# - CSP_NONCE_ALGORITHM: Specifies the algorithm used for generating nonce values.
# - CSP_REFERRER_POLICY: Sets the Referrer-Policy directive.
# - CSP_HSTS_MAX_AGE: Sets the HSTS (HTTP Strict Transport Security) max age in seconds.
# - CSP_HSTS_INCLUDE_SUBDOMAINS: If True, includes subdomains in HSTS.
# - CSP_HSTS_PRELOAD: Enables HSTS preloading.
# - CSP_FEATURE_POLICY: Specifies Feature-Policy directives.
# - CSP_X_CONTENT_TYPE_OPTIONS: Sets X-Content-Type-Options header to prevent MIME type sniffing.
# - CSP_X_FRAME_OPTIONS: Sets X-Frame-Options header to control framing permissions.
# - CSP_X_XSS_PROTECTION: Sets X-XSS-Protection header to prevent Cross-Site Scripting (XSS) attacks.

# Advanced Configuration...

# Advanced security configurations:
# - CSP_EXPECT_CT: Expect-CT directive configuration.
# - CSP_CROSS_ORIGIN_OPENER_POLICY: Cross-Origin-Opener-Policy directive configuration.
# - CSP_CROSS_ORIGIN_EMBEDDER_POLICY: Cross-Origin-Embedder-Policy directive configuration.
# - CSP_FORCE_HTTPS: If True, enforces HTTPS throughout the application.
# - CSP_REFERRER_POLICY_FEATURE: Enables Referrer-Policy directive feature.
# - CSP_REFERRER_POLICY_NO_REFERER: If True, omits Referer header if referring URL is insecure.
# - CSP_REFERRER_POLICY_NO_REFERRER_WHEN_DOWNGRADE: If True, omits Referer header when the referring URL is a downgrade from HTTPS to HTTP.

# Configure these settings according to your security requirements and application needs.

# Base Configuration... 

CSP_DIRECTIVES = { 'default-src': ["'self'"], 'style-src': ["'self'", "'unsafe-inline'"] }
CSP_REPORT_URI = ''
CSP_REPORT_ONLY = False
CSP_ENABLE_VIOLATION_HANDLING = False
CSP_REPORT_SAMPLE_WEIGHT = 0.0
CSP_VIOLATION_REPORT_ENDPOINT = '/violation-report'
CSP_LOG_FILE_PATH = 'csp_report.log'
CSP_SECURITY_HEADERS = None

# Additonal Configuration...

CSP_NONCE_LENGTH = 16
CSP_NONCE_ALGORITHM = 'sha256'
CSP_REFERRER_POLICY = "strict-origin-when-cross-origin"
CSP_HSTS_MAX_AGE = 31536000
CSP_HSTS_INCLUDE_SUBDOMAINS = True
CSP_HSTS_PRELOAD = False
CSP_FEATURE_POLICY = None
CSP_X_CONTENT_TYPE_OPTIONS = 'nosniff'
CSP_X_FRAME_OPTIONS = 'SAMEORIGIN'
CSP_X_XSS_PROTECTION = '1; mode=block'

# Advance Configuration...

CSP_EXPECT_CT = None
CSP_CROSS_ORIGIN_OPENER_POLICY = None
CSP_CROSS_ORIGIN_EMBEDDER_POLICY = None
CSP_FORCE_HTTPS = False
CSP_REFERRER_POLICY_FEATURE = False
CSP_REFERRER_POLICY_NO_REFERER = False
CSP_REFERRER_POLICY_NO_REFERRER_WHEN_DOWNGRADE = False

# CORS -> Cross-Origin Resource Sharing Configuration

# Note: Uncomment the following configurations in case of use.

# Basic CORS Configuration...

# CORS_ALLOWED_ORIGIN: Specifies the origins allowed for CORS requests. ["*"] allows all origins.
# CORS_ALLOWED_METHOD: Defines the HTTP methods permitted for CORS requests (e.g., ["GET", "POST"]).
# CORS_ALLOWED_HEADERS: Defines allowed headers for CORS requests. "*" allows all headers.
# CORS_ALLOWED_CREDENTIALS: If True, allows sending credentials (e.g., cookies, authorization headers) with CORS requests.
# CORS_EXPOSED_HEADERS: Specifies headers exposed to the client in CORS responses.
# CORS_MAX_AGE: Sets the maximum time (in seconds) that preflight requests can be cached.

# Additional CORS Configuration...

# Additional configurations for fine-tuning CORS handling:
# - CORS_PREFLIGHT_RESPONSE: Custom preflight response configuration.
# - CORS_PREFLIGHT_CACHE: If True, caches preflight responses.
# - CORS_ORIGIN_WHITELIST: Whitelists specific origins for CORS requests.
# - CORS_AUTOMATIC_PREFLIGHT_HANDLING: If True, automatically handles preflight requests.
# - CORS_DYNAMIC_HEADERS_WHITELIST: Whitelists specific dynamic headers for CORS requests.
# - CORS_LOG_REQUEST: If True, logs CORS requests.
# - CORS_RESPONSE_HANDLER: Handles custom responses when a CORS request is denied.
#   Pass the path to the function with arguments (request, origin, disallowed_headers).

# Customize these settings based on your application's CORS requirements and security policies.


# CORS_ALLOWED_ORIGIN = ["*"]
# CORS_ALLOWED_METHOD = ["GET", "POST"]
# CORS_ALLOWED_HEADERS = "*"
# CORS_ALLOWED_CREDENTIALS = False
# CORS_EXPOSED_HEADERS = "*"
# CORS_MAX_AGE = 1800
# CORS_SECURITY_HEADERS = {}
# CORS_EXCLUDE_PATHS = ['/']

# Additional CORS Configuration...

# CORS_PREFLIGHT_RESPONSE = None
# CORS_PREFLIGHT_CACHE = True
# CORS_ORIGIN_WHITELIST = None
# CORS_AUTOMATIC_PREFLIGHT_HANDLIGN = True
# CORS_DYNAMIC_HEADERS_WHITELIST = None
# CORS_LOG_REQUEST = True
# CORS_RESPONSE_HANDLER = [] # Handles custom response when a CORS request is denied, pass the path to the function :: arguments -> (request, origin, disallowed_headers)

ENVIROMENT = {
    'lxenviroment': ['packlib'] # add all the .lxe file in this list
}

############################################# NETIX ASGI SERVER SETTINGS #############################################

# Nextix server has not been configured with aquilify yet so these settings are not useful.

# Netix server setting...

HOST = ["127.0.0.1"]
PORT = 8000
SERVER_DEBUG = True
LOG_LEVEL = 'debug'
RELOAD = False
REUSE_PORT = True

# Either use host, port or uncomment this option
# BIND = "127.0.0.1:8000"

# Additional server settings ["Netix"]

BUFFER_RATE = 1669
UPLOAD_RATE = 10699
DOWNLOAD_RATE = 10699
MAX_HEADER_SIZE = 8192
REQUEST_TIMEOUT = 30 # (in seconds)

# Netix Production setting...
# By default these settings is commented uncomment it when use in prouction (deployement * )

# DAEMON_MODE = True
# MONITOR_CONSOLE = True
# BACKLOG = True
# ENCRYPTION = True
# NO_WEBSOCKET = True # false in case of websocket usage...
# SSL_CERT = [] # Pass your certificate path...
# SSL_KEY = [] # Pass you ssl key
# WORKERS = 1 ( By default it uses 1 worker to run the application change it according to you machine...)
# KEEPALIVE_CONNECTION = True 
# ROOT_PATH = "$script{}.packlib.json|os.path.join(__file__, 'packlib')"


