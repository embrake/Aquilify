from aquilify.core.schematic.routing import rule

from . import views, update, read, delete

ROUTER = [
    rule('/register', views.nosqlisertview, methods = ['GET', 'POST']),
    rule('/update', update.nosqlupdateview, methods = ['GET', 'POST']),
    rule('/read', read.nosqlreadview, methods = ['GET', 'POST']),
    rule('/delete', delete.nosqldeleteview, methods = ['GET', 'POST'])
]