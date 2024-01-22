from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

with open('LICENSE', 'r', encoding='utf-8') as f:
    license_text = f.read()

setup(
    name='aquilify',
    version='1.15',
    description="Aquilify is an ASGI (Asynchronous Server Gateway Interface) framework designed to facilitate the development of web applications with Python. It enables efficient handling of HTTP requests, WebSocket connections, middleware processing, and exception handling in an asynchronous environment.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Pawan kumar',
    author_email='embrakeproject@gmail.com',
    url='https://github.com/embrake/aquilify/',
    packages=find_packages(),
    keywords=['web framework', 'Python web development', 'user-friendly', 'high-level', 'ASGI', 'backend'],
    license='BSD-3-Clause',
    install_requires=['anyio'], 
    extras_require={
        'full': [
            'jinja2',
            'aiofiles',
            'python-multipart',
            'markupsafe'
        ],
        "sec": [
            "aiofiles",
            "markupsafe"
        ],
        "template": [
            "jinja2",
            "aiofiles"
        ]
    }, 
    entry_points={
        'console_scripts': [
            'aquilify = aquilify.build:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: AsyncIO',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: HTTP Servers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ]
)