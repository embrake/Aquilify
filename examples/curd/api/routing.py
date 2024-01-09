from aquilify.core.schematic.routing import rule

from . import view, update, read, delete

ROUTER = [
    rule('/register', view.insertview, methods = ['GET', 'POST']),
    rule('/update', update.updateview, methods = ['GET', 'POST']),
    rule('/read', read.readview, methods = ['GET', 'POST']),
    rule('/delete', delete.deleteview, methods = ['GET', 'POST']),
]