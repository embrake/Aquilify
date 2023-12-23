# Changelog

All notable changes to Aquilify will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
## [1.10] - 2023-11-16

### Added

- Initial release of version 1.10 of Aquilify.
- HTTP request handling and routing functionality.
- Support for asynchronous web applications using Python.
- Middleware support for preprocessing requests.
- WebSocket support for bidirectional communication.
- Exception handling mechanisms for graceful error responses.
- Basic documentation outlining framework features and installation.

## # f0001
## [1.11.0] - 2023-11-18

### Added

- Enhanced security features to mitigate potential vulnerabilities.
- Improved error handling for more descriptive and informative responses.
- Added support for custom exception handling.
- Performance optimizations for faster request processing.
- Expanded documentation with more detailed examples and usage scenarios.
- Integration with additional third-party libraries for extended functionality.
- Compatibility updates for Python 3.11 and the latest ASGI specifications.
- Added support for `AuthenticationMiddleware` - `BasicAuthMiddleware`

### Changed

- Updated dependencies to ensure compatibility and security.
- Added `Markupsafe` & `Anyio` dependencies.

### Fixed

- Resolved minor bugs related to WebSocket connections.
- Addressed edge cases in middleware processing for more consistent behavior.
- Fixed issues with URL routing in specific scenarios.
- Fixed import errors.
- Fixed middleware exclusion.
- Fixed `CSRF` middleware protecttion.

## Version 1.12.0
## # f0002
## [1.12.0] - 2023-12-16

### Added

- Robust HTTP routing handling
- Batteries-included middlestack framework
- View-based routing
- Jinja2 template rendering
- Pre-included middlewares
- Manage Aquilify app using settings.py

## Version 1.13.0
## # f0002
## [1.13.0] - 2023-12-18

# Fixed 

- Minor bug fixes.
- Resloved import error.