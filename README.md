<div align="center">
  <a href="#"><img src="https://i.ibb.co/hXF5Znx/IMG-20231115-232824.png" alt="IMG-20231115-232824" style="border-radius: 6px;" width="420px" alt="Aquilify"></a>
</div>

---

**Documentation**: [http://www.aquilify.vvfin.in/](http://aquilify.vvfin.in/)

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
## Dependencies


Aquilify only requires `anyio`, and the following are optional:

* [`aiofiles`][aiofile] - Required if you want to use the `StaticMIddleware` or `File based Opertation`.
* [`jinja2`][jinja2] - Required if you want to use `TemplateResponse`.
* [`python-multipart`][python-multipart] - Required if you want to support form parsing, with `request.form()`.
* [`itsdangerous`][itsdangerous] - Required for `SessionMiddleware` and `CSRF` support.
* [`markupsafe`][markupsafe] - Required for `Jinja2` and `CSRF` support.

You can install all of these with `pip3 install aquilify[full]`.

## Credits
This project uses code adapted from the Starlette framework.

<p align="center"><i>Aquilify is <a href="https://github.com/embrake/aquilify/blob/master/LICENSE">BSD licensed</a> code.<br/>Designed & crafted with care.</i></br>&mdash; ⭐️ &mdash;</p>