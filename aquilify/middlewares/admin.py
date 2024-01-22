from aquilify.wrappers import Request, Response
from aquilify.responses import HTMLResponse
from aquilify.settings import settings

class ConsoleAPI:
    def __init__(self, app) -> None:
        self.app = app
        self.prefix = getattr(settings, 'API_CONSOLE_URL', '/console')
        
    async def __call__(self, request: Request, response: Response):
        path: str = request.path
        self.methods = None

        if path.startswith(self.prefix):
            response = HTMLResponse(await self.html_data(request))
            return response
        return response
    
    async def html_data(self, request: Request):
        routes = self.app.routes

        javascript_code = """
            <script>
                async function fetchData(url, method, outputId, queryParams) {
                    const outputBox = document.getElementById(outputId);
                    outputBox.innerText = 'Loading...';
                    const headersBox = document.getElementById(outputId + '_headers');
                    headersBox.innerText = '';
                    const paramsBox = document.getElementById(outputId + '_params');
                    paramsBox.innerText = queryParams || 'No parameters';

                    try {
                        const response = await fetch(url, { method: method, timeout: 5000 });
                        const contentType = response.headers.get('content-type');
                        const headers = Object.fromEntries(response.headers);
                        const status = response.status;

                        headersBox.innerText = `HTTP Status: ${status}\n${JSON.stringify(headers, null, 2)}`;

                        let output = '';

                        if (contentType && contentType.includes('application/json')) {
                            output = await response.json();
                        } else {
                            output = await response.text();
                        }

                        outputBox.innerText = JSON.stringify(output, null, 2);
                        outputBox.style.display = 'block';
                        headersBox.style.display = 'block';
                        paramsBox.style.display = 'block';
                    } catch (error) {
                        if (error instanceof TypeError && error.message === 'Failed to fetch') {
                            outputBox.innerText = 'Error: Request timeout';
                        } else {
                            outputBox.innerText = `Error: ${error.message}`;
                        }
                        outputBox.style.display = 'block';
                    }
                }

                function clearResponseBoxes() {
                    const responseBoxes = document.querySelectorAll('.response-box');
                    responseBoxes.forEach(box => {
                        box.innerText = '';
                        box.style.display = 'none';
                    });

                    const headersBoxes = document.querySelectorAll('.headers-box');
                    headersBoxes.forEach(box => {
                        box.innerText = '';
                        box.style.display = 'none';
                    });

                    const paramsBoxes = document.querySelectorAll('.params-box');
                    paramsBoxes.forEach(box => {
                        box.innerText = 'No parameters';
                        box.style.display = 'none';
                    });
                }

                function changeMethod(url, method, outputId, contentType) {
                    const fetchButton = document.getElementById(`fetchButton_${outputId}`);
                    fetchButton.onclick = function() {
                        const payload = document.getElementById(`${outputId}_payload`).value;
                        fetchData(url, method, outputId, '{}', contentType, payload);
                    };
                }


                function expandCollapseAll(action) {
                    const headersBoxes = document.querySelectorAll('.headers-box');
                    headersBoxes.forEach(box => {
                        box.style.display = action;
                    });

                    const paramsBoxes = document.querySelectorAll('.params-box');
                    paramsBoxes.forEach(box => {
                        box.style.display = action;
                    });
                }
            </script>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    padding: 5px;
                    margin: 0;
                    background-color: #f5f5f5;
                    color: #333;
                    line-height: 1.6;
                }

                h2 {
                    text-align: center;
                    color: #444;
                    margin-bottom: 20px;
                }

                button {
                    padding: 10px 20px;
                    margin: 5px;
                    cursor: pointer;
                    background-color: rgb(7, 170, 235);
                    color: #fff;
                    border: none;
                    border-radius: 4px;
                    transition: background-color 0.3s;
                }

                button:hover {
                    background-color: #2980b9;
                }

                select {
                    padding: 8px;
                }

                .response-box, .headers-box, .params-box {
                    white-space: pre-wrap;
                    font-family: 'Courier New', monospace;
                    color: white;
                    padding: 10px;
                    margin-bottom: 10px;
                    background-color: black;
                    border-radius: 4px;
                    overflow: auto;
                    display: none;
                }

                .toggle-headers, .toggle-params {
                    cursor: pointer;
                    color: #3498db;
                    text-decoration: underline;
                    margin-left: 10px;
                }
            </style>
        """

        html_data = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>ConsoleAPI | AQUILIFY - v1.1</title>
            </head>
            <body>
                <h2>Welcome to AQUILIFY ConsoleAPI - v1.1</h2>
                <button onclick="expandCollapseAll('block')">Expand All</button>
                <button onclick="expandCollapseAll('none')">Collapse All</button>
                <h3>Available Routes:</h3>
        """

        for index, route in enumerate(routes):
            path, methods, _, _, _, _ = route
            path = self.convert_regex_path(path)
            output_id = f"response_{index}"  # Unique ID for each output box
            
            # HTML for each route container
            route_html = f"""
                <div style="background-color: #f5f5f5; padding: 20px; margin-bottom: 10px;">
                    <h4>PATH - '{path}' & URL - <u>{request.scheme}://{request.host}{path}</u></h4>
                    <div>
                        <label for="method_{index}">Method:</label>
                        <select id="method_{index}" onchange="changeMethod('{request.scheme}://{request.host}{path}', this.value, '{output_id}')">
            """

            for method in methods:
                route_html += f"<option value='{method}'>{method}</option>"

            route_html += "</select></div>"
            route_html += f"""
                <div>
                    <button onclick="fetchData('{request.scheme}://{request.host}{path}', document.getElementById('method_{index}').value, '{output_id}', '{str(request.query_params)}')">Fetch</button>
                    <span class="toggle-headers" onclick="document.getElementById('{output_id + '_headers'}').style.display = (document.getElementById('{output_id + '_headers'}').style.display === 'block' ? 'none' : 'block')">Headers</span>
                    <span class="toggle-params" onclick="document.getElementById('{output_id + '_params'}').style.display = (document.getElementById('{output_id + '_params'}').style.display === 'block' ? 'none' : 'block')">Params</span>
                </div>
                <div id="{output_id}" class="response-box"></div>
                <div id="{output_id + '_headers'}" class="headers-box"></div>
                <div>
                    <div id="{output_id + '_params'}" class="params-box">Query Params: {str(request.query_params)}</div>
                </div>
            """

            route_html += "</div>"  # Close the route container
            html_data += route_html  # Append the route HTML to the main HTML

        # Finish the main HTML data
        html_data += """
                <button onclick="clearResponseBoxes()">Clear All Responses</button>
            </body>
            </html>
        """

        final_data = f"{javascript_code}{html_data}"  # Combine JavaScript and HTML
        return final_data

    def convert_regex_path(self, path):
        return path[1:-1] if path.startswith('^') and path.endswith('$') else path