ROUTING = """from aquilify.core.routing import rule

# ROUTER configuration.

# The `ROUTER` list routes URLs to views.
# Examples:
# Function views
#     1. Add an import:  from my_app import views
#     2. Add a URL to ROUTER:  rule('/', views.home, name='home')
# Including another ROUTING
#     1. Import the include() function: from aquilify.core.routing import include, rule
#     2. Add a URL to ROUTER:  rule('/blog', include = include('blog.routing'))

ROUTER = [
    ... # add all your rule's here.
]
"""