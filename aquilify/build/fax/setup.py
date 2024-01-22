CONFIG_CFG = """[Aquilify]
path = /home/pawan/PythonProjects/testproject/myapp
project_name = myapp
version = 1.13
compiler_path = /home/pawan/PythonProjects/testproject/myapp/.aquilify
settings = /home/pawan/PythonProjects/testproject/myapp/settings.py

[ASGI_SERVER]
server = NETIX
host = 0.0.0.0
port = 8000
debug = True
reload = False
instance = asgi:app
"""