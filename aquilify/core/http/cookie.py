from http import cookies

SimpleCookie = cookies.SimpleCookie


def parse_cookie(cookie):
    cookiedict = {}
    for chunk in cookie.split(";"):
        if "=" in chunk:
            key, val = chunk.split("=", 1)
        else:
            key, val = "", chunk
        key, val = key.strip(), val.strip()
        if key or val:
            cookiedict[key] = cookies._unquote(val)
    return cookiedict
