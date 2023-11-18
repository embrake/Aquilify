<div align="center">
  <a href="#"><img src="https://i.ibb.co/hXF5Znx/IMG-20231115-232824.png" alt="IMG-20231115-232824" style="border-radius: 6px;" width="420px" alt="Aquilify"></a>
</div>

---

**Documentation**: [https://www.aquilify.vvfin.in/](http://aquilify.vvfin.in/)

---

# Aquilify

Aquilify is an ASGI (Asynchronous Server Gateway Interface) framework designed to facilitate the development of web applications with Python. It enables efficient handling of HTTP requests, WebSocket connections, middleware processing, and exception handling in an asynchronous environment.

## Introduction

"Aquilify" epitomizes a Python ASGI framework crafted to encapsulate the agility, strength, and precision reminiscent of eagles. This framework symbolizes a software architecture meticulously engineered for adaptability, streamlined processing, and unwavering robustness, drawing inspiration from the remarkable traits associated with eagles in the natural world.

Leveraging Python's asynchronous capabilities, Aquilify furnishes a resilient and expandable infrastructure tailored for crafting web applications. Offering an array of functionalities including request routing, seamless middleware support, WebSocket management, and proficient response handling, Aquilify is poised to empower developers in creating responsive and scalable web solutions.

## Why Choose Aquilify?

Aquilify was selected for its comprehensive support for asynchronous web application development in Python. Its key features, including robust HTTP request handling, WebSocket support, middleware capabilities, and exceptional exception handling, align perfectly with the project's requirements. The simplicity of defining routes, coupled with its scalability and community support, made Aquilify the ideal choice for empowering the development of modern, high-performance web applications.

## Key Features

- **HTTP Request Handling:** Aquilify efficiently processes incoming HTTP requests and provides a structured approach for defining routes and handling various HTTP methods (GET, POST, PUT, DELETE, etc.).

- **WebSocket Support:** The framework supports WebSocket connections, allowing bidirectional communication between clients and servers.

- **Middleware Processing:** Aquilify facilitates the use of middleware functions to preprocess requests, perform authentication, logging, or modify responses before sending them back.

- **Exception Handling:** The framework includes mechanisms to handle exceptions raised during request processing, enabling graceful error responses.

## Installation

```bash
pip install aquilify
```

You'll also want to install an ASGI server, such as [netix](), [uvicorn](http://www.uvicorn.org/), [daphne](https://github.com/django/daphne/), or [hypercorn](https://pgjones.gitlab.io/hypercorn/).

```shell
$ pip install netix
```

- Netix is an ASGI Web server gateway for Aquilify, built on the top of asynchronous programming.
## A Smiple Example

```python
# save this as main.py
from aquilify.core import Aquilify

app = Aquilify()

@app.route('/')
async def home():
    return {"message": "Welcome to Aquilify"}
```
## Terminal

```python
$ netix --deubg main:app
  * Starting Netix v1.12 (cpython 3.11.6, linux)
    -----------------------------------------------------------------------
    Options:
    run(host=127.0.0.1, port=8080, reuse_port=True, worker_num=1, reload=True, app=lo:app, log_level=DEBUG)
    -------------------------------- ---------------------------------------
    [2023-11-15 22:25:18] Starting Netix as an ASGI server for: Aquilify
    [2023-11-15 22:25:18,079] INFO: lifespan: startup
    [2023-11-15 22:25:18,080] INFO: lifespan.startup.complete
    [2023-11-15 22:25:19] Netix (ASGI) (pid 18513) is started at 127.0.0.1 port 8080
```

## Dependencies


Aquilify only requires `anyio`, and the following are optional:

* [`aiofiles`][aiofile] - Required if you want to use the `StaticMIddleware` or `File based Opertation`.
* [`jinja2`][jinja2] - Required if you want to use `TemplateResponse`.
* [`python-multipart`][python-multipart] - Required if you want to support form parsing, with `request.form()`.
* [`itsdangerous`][itsdangerous] - Required for `SessionMiddleware` and `CSRF` support.
* [`markupsafe`][markupsafe] - Required for `Jinja2` and `CSRF` support.

You can install all of these with `pip3 install aquilify[full]`.

## Benchmark Results

### Performance Overview

Comparative performance results for Quart, FastAPI, and Aquilify:

| Framework   | Requests/s | Mean Time/Request (ms) | Mean Time/Request (across all concurrent requests) | Transfer Rate (Kbytes/sec) |
|-------------|------------|------------------------|----------------------------------------------------|----------------------------|
| Aquilify    | 2210.25    | 1357.313               | 0.452                                              | 451.12                     |
| Quart       | 1202.38    | 2495.054               | 0.832                                              | 220.75                     |
| FastAPI     | 1682.11    | 1783.471               | 0.594                                              | 269.40                     |

### Test Details

#### Quart
- **Server Software:** hypercorn-h11
- **Server Hostname:** localhost
- **Server Port:** 8050
- **Document Path:** /api/10
- **Document Length:** 40 bytes
- **Concurrency Level:** 3000
- **Time Taken for Tests:** 24.951 seconds
- **Complete Requests:** 30000
- **Failed Requests:** 0
- **Total Transferred:** 5640000 bytes
- **HTML Transferred:** 1200000 bytes

#### FastAPI
- **Server Software:** uvicorn
- **Server Hostname:** localhost
- **Server Port:** 8080
- **Document Path:** /api/10
- **Document Length:** 39 bytes
- **Concurrency Level:** 3000
- **Time Taken for Tests:** 17.835 seconds
- **Complete Requests:** 30000
- **Failed Requests:** 0
- **Total Transferred:** 4920000 bytes
- **HTML Transferred:** 1170000 bytes

#### Aquilify
- **Server Software:** Netix
- **Server Hostname:** localhost
- **Server Port:** 8000
- **Document Path:** /api/10
- **Document Length:** 40 bytes
- **Concurrency Level:** 3000
- **Time Taken for Tests:** 13.573 seconds
- **Complete Requests:** 30000
- **Failed Requests:** 0
- **Total Transferred:** 6270000 bytes
- **HTML Transferred:** 1200000 bytes

### Observations

- **Aquilify** stands out with the highest requests per second, showcasing exceptional performance under heavy load.
- **Quart**, while demonstrating a lower request rate, performs competitively compared to FastAPI.
- **FastAPI** shows commendable performance metrics but falls between Quart and Aquilify in terms of throughput.
- **Aquilify** exhibits the lowest mean time per request, indicating faster request processing compared to the other frameworks.
- Detailed connection times highlight **Aquilify's efficiency** in handling concurrent requests, making it an optimal choice for high-throughput applications.

<p align="center"><i>Aquilify is <a href="https://github.com/embrake/aquilify/blob/master/LICENSE">BSD licensed</a> code.<br/>Designed & crafted with care.</i></br>&mdash; ⭐️ &mdash;</p>
