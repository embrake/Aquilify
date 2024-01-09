from aquilify.shortcuts import render

# Define all your views here.

async def homeview() -> dict:
    return {
        "response": "Available API Rule's ('/api/', '/nosql/')",
        "operations": ['create', 'update', 'read', 'delete'],
        "databases": ['sqlite3', 'electrus(nosql)']
    }, 200