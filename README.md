
<div align="center">
  <a href="#"><img src="https://i.ibb.co/jTwBsqH/aquilify.png" alt="IMG-20231115-232824" style="border-radius: 6px;" width="420px" alt="Aquilify"></a>
</div>

---

**Documentation**: [http://www.aquilify.vvfin.in/](http://aquilify.vvfin.in/)

---

# AQUILIFY

Aquilify is an ASGI (Asynchronous Server Gateway Interface) framework designed to facilitate the development of web applications with Python. It enables efficient handling of HTTP requests, WebSocket connections, middleware processing, and exception handling in an asynchronous environment.

## Installation

```bash
$ pip install aquilify
```

##### Or you can install the `aquilify[full]`

```bash
$ pip install aquilify[full]
```

## Basic Setup

Create a new aquilify app using the command show below :

```bash
$ aquilify create-app myapp
```
Now, move inside the `myapp` and run :

```bash
$ aquilify runserver
```

To make changes in ASGI server configuration open `myapp/config.cfg` :

#### Default Configuration :

```python
[ASGI_SERVER]
server = NETIX
host = 127.0.0.1
port = 8000
debug = True
reload = False
instance = asgi:application
```

visit: `http://localhost:8000`

output: 
<div align="center">
  <a href="#"><img src="https://i.ibb.co/Yy8sX0q/setup.png" alt="IMG-20231115-232824" style="border-radius: 6px;" width="420px" alt="Aquilify"></a>
</div>

## Creating views

`myapp/views.py`

```python

async def myview() -> dict:
  return {"message": "Welcome to aquilify"}, 200
```

`myapp/routing.py`

```python
from aquilify.core.routing import rule

import views

ROUTER = [
  rule('/', view.myview)
]
```

`run server`

```bash
$ aquilify runserver
```

```python
Starting Netix v1.12 (cpython 3.12.1, win32)
------------------------------------------------------------------------
Options:
  run(host=127.0.0.1, port=8000, reuse_port=True, worker_num=1, ssl={}, debug=True, app=asgi:application, log_level=DEBUG)
------------------------------------------------------------------------
[2024-01-08 15:48:19] Netix detected Aquilify starting.. : Aquilify
[2024-01-08 15:48:19,421] INFO: lifespan: startup
[2024-01-08 15:48:19,423] INFO: lifespan.startup.complete
[2024-01-08 15:48:20] Netix (ASGI) (pid 17892) is started at 127.0.0.1 port 8000
```

`output` : `http://localhost:8000/` :

```json
{
    "message": "Welcome to aquilify"
}
```

## Credits
- Thanks to `starlette`.
- This project uses code adapted from the Starlette framework.

## Dependencies


Aquilify only requires `anyio`, and the following are optional:

* [`aiofiles`][aiofile] - Required if you want to use the `StaticMIddleware` or `File based Opertation`.
* [`jinja2`][jinja2] - Required if you want to use `TemplateResponse`.
* [`python-multipart`][python-multipart] - Required if you want to support form parsing, with `request.form()`.
* [`itsdangerous`][itsdangerous] - Required for `SessionMiddleware` and `CSRF` support.
* [`markupsafe`][markupsafe] - Required for `Jinja2` and `CSRF` support.