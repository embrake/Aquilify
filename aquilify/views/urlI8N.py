def urlI8N():
    html_code = f'''
    <!doctype html>
    <html lang="en-us" dir="ltr">
        <head>
            <meta charset="utf-8">
            <title>The install worked successfully! Congratulations!</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                .logo,h1{{font-size:1.375rem}}
                .option,footer{{display:grid;box-sizing:border-box}}
                .logo,.option{{text-decoration:none}}
                .option p,main p{{line-height:1.25}}
                a{{color:red}}
                header{{border-bottom:1px solid #efefef;display:grid;grid-template-columns:auto auto;align-items:self-end;justify-content:space-between;gap:7px;padding-top:20px;padding-bottom:10px}}
                body{{max-width:960px;color:#525252;font-family:"Segoe UI",system-ui,sans-serif;margin:0 auto}}
                main{{text-align:center}}
                h1,h2,h3,h4,h5,p,ul{{padding:0;margin:0;font-weight:400}}
                .logo{{font-weight:700}}
                .figure{{margin-top:19vh;max-width:265px;position:relative;z-index:-9;overflow:visible}}
                .exhaust__line{{animation:70ms ease-in-out 100 alternate thrust}}
                .smoke{{animation:.1s ease-in-out 70 alternate smoke}}
                @keyframes smoke{{0%{{transform:translate3d(-5px,0,0)}}100%{{transform:translate3d(5px,0,0)}}}}
                .flame{{animation:.1s ease-in-out 70 alternate burnInner2}}
                @keyframes burnInner2{{0%{{transform:translate3d(0,0,0)}}100%{{transform:translate3d(0,3px,0)}}}}
                @keyframes thrust{{0%{{opacity:1}}100%{{opacity:.5}}}}
                @media (prefers-reduced-motion:reduce){{.exhaust__line,.flame,.smoke{{animation:none}}}}
                h1{{max-width:32rem;margin:5px auto 0}}
                main p{{max-width:26rem;margin:15px auto 0}}
                footer{{grid-template-columns:1fr 1fr 1fr;gap:5px;padding:25px 0;position:fixed;left:50%;bottom:0;width:960px;transform:translateX(-50%);transform-style:preserve-3d;border-top:1px solid #efefef}}
                .option{{grid-template-columns:min-content 1fr;gap:10px}}
                .option svg{{width:1.5rem;height:1.5rem;fill:gray;border:1px solid #d6d6d6;padding:5px;border-radius:100%}}
                .option p{{font-weight:300;color:#525252;display:table}}
                .option .option__heading{{color:red;font-size:1.25rem;font-weight:400}}
                @media (max-width:996px){{body,footer{{max-width:780px}}}}
                @media (max-width:800px){{footer,header{{grid-template-columns:1fr}}footer{{height:100%;gap:60px;position:relative;padding:25px;width:100%;margin-top:50px}}.figure{{margin-top:10px}}main{{padding:0 25px}}main h1{{font-size:1.25rem}}header{{padding-left:20px;padding-right:20px}}}}
                @media (min-width:801px) and (max-height:730px){{.figure{{margin-top:80px}}}}
                @media (min-width:801px) and (max-height:600px){{footer{{position:relative;margin:135px auto 0}}.figure{{margin-top:50px}}}}
                .sr-only{{clip:rect(1px,1px,1px,1px);clip-path:inset(50%);height:1px;overflow:hidden;position:absolute;white-space:nowrap;width:1px}}
            </style>
        </head>
        <body>
        <header>
            <a class="logo" href="https://www.aquilify.vvfin.in/" target="_blank" rel="noopener">
                Aquilify
            </a>
            <p>View <a href="" target="_blank" rel="noopener">release notes</a> for Aquilify 1.13</p>
        </header>
        <main>
            <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="640" height="480" viewBox="0 0 640 480" xml:space="preserve">
                <defs>
                </defs>
                <g transform="matrix(1 0 0 1 0 0)"  >
                <g style=""   >
                </g>
                </g>
                <g transform="matrix(1.43 0 0 1.43 307.97 231.91)"  >
                <g style=""   >
                        <g transform="matrix(1 0 0 1 0.02 0.02)"  >
                <path style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(231,34,39); fill-rule: nonzero; opacity: 1;"  transform=" translate(-61.46, -61.46)" d="M 61.44 0 A 61.46 61.46 0 1 1 18 18 A 61.25 61.25 0 0 1 61.44 0 Z M 96.75 26.13 a 49.93 49.93 0 1 0 14.63 35.31 A 49.76 49.76 0 0 0 96.75 26.13 Z" stroke-linecap="round" />
                </g>
                        <g transform="matrix(1 0 0 1 -0.01 0)"  >
                <path style="stroke: none; stroke-width: 1; stroke-dasharray: none; stroke-linecap: butt; stroke-dashoffset: 0; stroke-linejoin: miter; stroke-miterlimit: 4; fill: rgb(38,38,38); fill-rule: nonzero; opacity: 1;"  transform=" translate(-61.43, -61.44)" d="M 69.6 51.38 h 11 A 2.9 2.9 0 0 1 83 55.89 L 56.78 100.67 a 2.89 2.89 0 0 1 -5.3 -2.07 l 3.87 -27.48 l -13.05 0.22 a 2.88 2.88 0 0 1 -2.93 -2.83 a 3 3 0 0 1 0.4 -1.51 L 65.59 22.23 a 2.89 2.89 0 0 1 5.34 1.87 L 69.6 51.38 Z" stroke-linecap="round" />
                </g>
                </g>
                </g>
                </svg>
            <h1>The install worked successfully! Congratulations!</h1>
            <p>You are seeing this page because <a href="" target="_blank" rel="noopener">DEBUG=True</a> is in your settings file and you have not configured any Constructors.</p>
        </main>
        </body>
    </html>
    '''
    return html_code
