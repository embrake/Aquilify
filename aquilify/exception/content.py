# HTML Exception Content for web rendring...

from __future__ import annotations

def exceptions(error_message: str, formatted_traceback: str, underlined_line: str,
               error_type: str, file_and_line: str, code_lines: str, system_info: dict, req_data: dict = None):
    max_key_length = max(len(key) for key in system_info)
    max_value_length = max(len(str(value)) for value in system_info.values())
    padding = 4

    system_info_content = '\n'.join([
        '{}: {}'.format(key.ljust(max_key_length + padding), str(value).ljust(max_value_length))
        for key, value in system_info.items()
    ])
    
    req_info = ''
    if req_data is not None:
        max_key_req = max(len(key) for key in req_data)
        max_value_req = max(len(str(value)) for value in req_data.values())
        req_padding = 4

        req_info = '\n'.join([
            '{}: {}'.format(key.ljust(max_key_req + req_padding), str(value).ljust(max_value_req))
            for key, value in req_data.items()
        ])

    html_content = """
<html>
<head>
    <title>{error_type}: {error_message}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
     body {{font-family: Arial, sans-serif;background-color: white;margin: 0;padding: 0;display: flex;justify-content: center;align-items: center;overflow-x: hidden;}}
    .container {{background-color: white;padding: 20px;text-align: center;width: 100%;max-width: none;height: 100%;max-height: auto;}}h1
    {{color: black;margin-bottom: 20px;font-family: 'Courier New', monospace;font-size: 32px;}}
    .error-message {{margin-bottom: 20px;font-size: 18px;font-family: 'Courier New', monospace;white-space: pre-wrap;}}pre 
    {{white-space: pre-wrap;background-color: #f9f9f9;padding: 15px;border-radius: 3px;border: 1px solid #ddd;text-align: left;font-size: 16px;overflow-y: auto;}}
    @media (max-width: 768px) {{body {{padding: 20px;height: 120vh;}}h1 {{font-size: 24px;}}.error-message
    {{font-size: 16px;}}pre {{font-size: 14px;}}.message-tool {{font-size: 14px;}}}}@media (max-width: 480px) 
    {{body {{padding: 20px;}}h1 {{font-size: 20px;}}.error-message {{font-size: 14px;}}pre {{font-size: 12px;}}.message-tool 
    {{font-size: 14px;}}}}@media (max-width: 320px) {{body {{padding: 20px;height: auto;}}h1 {{font-size: 18px;}}.error-message 
    {{font-size: 12px;}}pre {{font-size: 10px;}}.message-tool {{font-size: 14px;}}}}
    </style>
</head>
<body>
    <div class="container">
        <h1>{error_type}</h1>
        <p class='error-message'><b style="color: red;">{error_type}</b>: {error_message}</p>
        <h2 style="font-family: 'Courier New', monospace;">Traceback</h2>
        <p style="color: red; font-size: smaller; font-family: 'Courier New', monospace; text-align: left; margin: 10px 0; word-wrap: break-word;">
            <u style="color: red;">{file_and_line}</u>
        </p>
        <pre>Object:{underlined_line}</pre>
        <h2 style="font-family: 'Courier New', monospace;">Traceback | Formatted</h2>
        <pre>{formatted_traceback}</pre>
        <h2 style="font-family: 'Courier New', monospace;">Traceback | Detailed</h2>
        <pre>{code_lines}</pre>
        <h2 style="font-family: 'Courier New', monospace;">Request Information</h2>
        <pre id="systemInfoOutput">{request_info}</pre>
        <h2 style="font-family: 'Courier New', monospace;">META</h2>
        <pre id="systemInfoOutput">{system_info_content}</pre>
        <p class="message-tool" style="text-align: left; color: #2F4F4F;">
            The Evelax caught an exception in your ASGI application. You can now look at the traceback which led to the error.
        </p>
        <p class="message-tool" style="text-align: left; color: #2F4F4F;">
            A traceback interpreter is a tool that helps developers understand and diagnose errors in their code. It provides a detailed history of function calls leading to an error. Building a custom traceback interpreter offers several advantages:
        </p>
        <ul class="message-tool" style="text-align: left; color: #2F4F4F;">
            <li><b>Traceback Generation:</b> Analyze the call stack to collect function call information.</li>
            <li><b>Formatting:</b> A human-readable traceback message with error details.</li>
        </ul>
        <p class="message-tool" style="text-align: right; color: #708090;">
            Powered  by <b>Evelax</b>, your friendly <b>Aquilify</b> powered traceback interpreter.
        </p>
        <br>
    </div>
</body>
</html>
""".format(
        error_type=error_type,
        error_message=error_message,
        file_and_line=file_and_line,
        underlined_line=underlined_line,
        formatted_traceback=formatted_traceback,
        code_lines=code_lines,
        request_info=req_info,
        system_info_content=system_info_content
    )

    return html_content
    
def error404():
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>404 - Not Found</title>
  <style>
    body{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}
    .error-container{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}
    h1{font-size:2.5em;color:#333;margin-bottom:20px;}
    p{color:#555;font-size:1.2em;margin-bottom:30px;}
    a{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}
    a:hover{background-color:#555;}
    @media (max-width:768px){.error-container{padding:20px;}h1{font-size:2em;}p{font-size:1em;margin-bottom:20px;}a{padding:10px 20px;}}
  </style>
</head>
<div class="error-container">
  <h1>404 - Not Found</h1>
  <p>The requested page could not be found.</p>
</div>
</body>
</html>

"""
    return html

def error405():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Error 405 - Method Not Allowed</title>
  <style>
    body{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}
    .error-container{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}
    h1{font-size:2.5em;color:#333;margin-bottom:20px;}
    p{color:#555;font-size:1.2em;margin-bottom:30px;}
    a{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}
    a:hover{background-color:#555;}
    @media (max-width:768px){.error-container{padding:20px;}h1{font-size:2em;}p{font-size:1em;margin-bottom:20px;}a{padding:10px 20px;}}
  </style>
</head>
<body>
  <div class="error-container">
    <h1>405 - Method Not Allowed</h1>
    <p>Sorry, the method used in the request is not allowed on this server.</p>
  </div>
</body>
</html>
"""

def error500(detail):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>500 - Internal Server Error</title>
  <style>
    body{{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}}
    .error-container{{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}}
    h1{{font-size:2.5em;color:#333;margin-bottom:20px;}}
    p{{color:#555;font-size:1.2em;margin-bottom:30px;}}
    a{{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}}
    a:hover{{background-color:#555;}}
    @media (max-width:768px){{.error-container{{padding:20px;}}h1{{font-size:2em;}}p{{font-size:1em;margin-bottom:20px;}}a{{padding:10px 20px;}}}}
  </style>
</head>
<body>
<div class="error-container">
  <h1>500 - {detail}</h1>
  <p>Sorry, there was an internal server error.</p>
  <a href="/">Back to Home</a>
</div>
</body>
</html>
"""


def error403(data):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>403 - Forbidden</title>
  <style>
    body{{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}}
    .error-container{{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}}
    h1{{font-size:2.5em;color:#333;margin-bottom:20px;}}
    p{{color:#555;font-size:1.2em;margin-bottom:30px;}}
    a{{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}}
    a:hover{{background-color:#555;}}
    @media (max-width:768px){{.error-container{{padding:20px;}}h1{{font-size:2em;}}p{{font-size:1em;margin-bottom:20px;}}a{{padding:10px 20px;}}}}
  </style>
</head>
<div class="error-container">
  <h1>403 - Forbidden | {data} </h1>
  <p>The server received too many requests.</p>
</div>
</body>
</html>
"""

def error400():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>400 - Bad Request</title>
  <style>
    body{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}
    .error-container{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}
    h1{font-size:2.5em;color:#333;margin-bottom:20px;}
    p{color:#555;font-size:1.2em;margin-bottom:30px;}
    a{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}
    a:hover{background-color:#555;}
    @media (max-width:768px){.error-container{padding:20px;}h1{font-size:2em;}p{font-size:1em;margin-bottom:20px;}a{padding:10px 20px;}}
  </style>
</head>
<div class="error-container">
  <h1>400 - Bad Request</h1>
  <p>There was a bad request sent to the server.</p>
</div>
</body>
</html>
"""

def error502():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>502 - Bad Gateway</title>
  <style>
    body{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}
    .error-container{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}
    h1{font-size:2.5em;color:#333;margin-bottom:20px;}
    p{color:#555;font-size:1.2em;margin-bottom:30px;}
    a{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}
    a:hover{background-color:#555;}
    @media (max-width:768px){.error-container{padding:20px;}h1{font-size:2em;}p{font-size:1em;margin-bottom:20px;}a{padding:10px 20px;}}
  </style>
</head>
<div class="error-container">
  <h1>502 - Bad Gateway</h1>
  <p>The server received an invalid response from the upstream server.</p>
</div>
</body>
</html>
"""

def error429(data):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>429 - To Many Request</title>
  <style>
    body{{font-family:'Arial',sans-serif;margin:0;display:flex;justify-content:center;align-items:center;height:100vh;background-color:#f5f5f5;}}
    .error-container{{text-align:center;background-color:#f5f5f5;padding:40px;border-radius:8px;max-width:80%;}}
    h1{{font-size:2.5em;color:#333;margin-bottom:20px;}}
    p{{color:#555;font-size:1.2em;margin-bottom:30px;}}
    a{{text-decoration:none;background-color:#333;color:#fff;padding:12px 24px;border-radius:5px;transition:background-color 0.3s;}}
    a:hover{{background-color:#555;}}
    @media (max-width:768px){{.error-container{{padding:20px;}}h1{{font-size:2em;}}p{{font-size:1em;margin-bottom:20px;}}a{{padding:10px 20px;}}}}
  </style>
</head>
<div class="error-container">
  <h1>429 - To Many Request | {data} </h1>
  <p>The server received too many requests.</p>
</div>
</body>
</html>
"""