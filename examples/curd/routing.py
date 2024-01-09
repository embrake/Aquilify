from aquilify.core.routing import rule, include

import views

ROUTER = [
    rule('/', views.homeview),
    rule('/api', include = include("api.routing"), methods = ['GET', 'POST']),
    rule('/nosql', include = include("nosql.routing"), methods = ['GET', 'POST'])
]