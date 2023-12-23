def debug_404(links, data):
    html_code = f'''
    <!DOCTYPE html>
    <html lang="en">

    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>404 Error - Page Not Found</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:Arial,sans-serif;background-color:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh;}}
        .container{{width:80%;text-align:center;}}
        h1{{font-size:4em;margin-bottom:20px;color:#333;}}
        .error-details{{background-color:#FFFACD;padding:30px;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,0.1);}}
        .debugging-info{{text-align:left;margin-top:30px;}}
        .debugging-info h2{{font-size:2em;margin-bottom:15px;color:#333;}}
        .debugging-info p{{margin-bottom:10px;font-size:1.2em;}}
        .debugging-info p span{{font-weight:bold;}}
        .routing-pattern-box,.warning-box{{margin-top:20px;padding:15px;border-radius:5px;}}
        .routing-pattern-box{{background-color:#FFFACD;border:1px solid black;}}
        .routing-pattern-box h3,.warning-box h3{{font-size:1.5em;margin-bottom:10px;color:black;}}
        .routing-pattern-box ul{{list-style:none;padding:0;text-align:left;}}
        .routing-pattern-box ul li{{margin-bottom:8px;color:#555;}}
        .warning-box{{background-color:#ffeaea;border:1px solid #e74c3c;}}
        .warning-box p{{color:#e74c3c;font-weight:bold;font-size:1.2em;}}
        .warning-box p:before{{content:"⚠ ";}}
        p.message{{margin-top:30px;font-size:1.1em;color:#555;}}
        @media only screen and (max-width:768px){{h1{{font-size:3em;}}.debugging-info h2{{font-size:1.5em;}}.debugging-info p{{font-size:1em;}}.routing-pattern-box h3,.warning-box h3{{font-size:1.2em;}}.warning-box p{{font-size:1em;}}p.message{{font-size:0.9em;}}}}
    </style>
    </head>

    <body>
    <div class="container">
        <h1>404 - Page Not Found</h1>
        <div class="error-details">
        <div class="debugging-info">
            <h2>Debugging Details:</h2>
            <p>Requested Method: <span>{data['method']}</span></p>
            <p>Requested URL: <span>{data['url']}</span></p>
            <p>User's IP Address: <span>{data['client_ip']}</span></p>
            <p>User Agent: <span>{data['user_agent']}</span></p>
            <div class="routing-pattern-box">
            <h3>Routing Pattern:</h3>
            <ul>
                {''.join([f'<b><li>Name: {name} | | Path: {path}</li></b>' for path, _, name in links])}
            </ul>
            </div>
            <div class="warning-box">
            <h3>Warning:</h3>
            <p>Current path "{data['path']}" not found in Routing Pattern!</p>
            </div>
            <p class="message">You're seeing this error because you have DEBUG = True in Aquilify settings. Change that to false to display the standard 404 error page.</p>
        </div>
        </div>
    </div>
    </body>

    </html>
    '''
    return html_code

def debug_405(data):
    html_code = f'''
    <!DOCTYPE html>
    <html lang="en">

    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>405 Error - Method Not Allowed</title>
    <style>
        *{{margin:0;padding:0;box-sizing:border-box;}}
        body{{font-family:Arial,sans-serif;background-color:#f4f4f4;display:flex;justify-content:center;align-items:center;height:100vh;}}
        .container{{width:80%;text-align:center;}}
        h1{{font-size:4em;margin-bottom:20px;color:#333;}}
        .error-details{{background-color:#FFFACD;padding:30px;border-radius:8px;box-shadow:0 0 10px rgba(0,0,0,0.1);}}
        .debugging-info{{text-align:left;margin-top:30px;}}
        .debugging-info h2{{font-size:2em;margin-bottom:15px;color:#333;}}
        .debugging-info p{{margin-bottom:10px;font-size:1.2em;}}
        .debugging-info p span{{font-weight:bold;}}
        .warning-box{{background-color:#ffeaea;border:1px solid #e74c3c;padding:15px;border-radius:5px;}}
        .warning-box h3{{font-size:1.5em;margin-bottom:10px;color:#e74c3c;}}
        .warning-box p{{color:#e74c3c;font-weight:bold;font-size:1.2em;}}
        .warning-box p:before{{content:"⚠ ";}}
        p.message{{margin-top:30px;font-size:1.1em;color:#555;}}
        @media only screen and (max-width:768px){{h1{{font-size:3em;}}.debugging-info h2{{font-size:1.5em;}}.debugging-info p{{font-size:1em;}}.warning-box h3{{font-size:1.2em;}}.warning-box p{{font-size:1em;}}p.message{{font-size:0.9em;}}}}
    </style>
    </head>

    <body>
    <div class="container">
        <h1>405 - Method Not Allowed</h1>
        <div class="error-details">
        <div class="debugging-info">
            <h2>Debugging Details:</h2>
            <p>Requested Method: <span>{data['method']}</span></p>
            <p>Requested URL: <span>{data['url']}</span></p>
            <p>Allowed Methods : <span>{data['allowed_method']}</span></p>
            <p>User's IP Address: <span>{data['client_ip']}</span></p>
            <p>User Agent: <span>{data['user_agent']}</span></p>
            <div class="warning-box">
            <h3>Warning:</h3>
            <p>Method not allowed for the requested URL!</p>
            </div>
            <p class="message">You're seeing this error because you have DEBUG = True in Aquilify settings. Change that to false to display the standard 405 error page.</p>
        </div>
        </div>
    </div>
    </body>

    </html>
    '''

    return html_code
