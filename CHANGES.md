## [1.11.0] - 2023-11-18

### Added

- Implemented advanced security features to fortify the application against potential vulnerabilities, ensuring a robust defense mechanism.
- Enhanced error handling for more detailed and informative responses, providing users with meaningful insights into encountered issues.
- Introduced support for custom exception handling, empowering developers to tailor error management to specific application needs.
- Executed performance optimizations to significantly expedite request processing, resulting in a more responsive system.
- Expanded documentation with comprehensive examples and usage scenarios, offering developers thorough guidance.
- Integrated additional third-party libraries, further extending the platform's functionality and versatility.
- Ensured compatibility with Python 3.11 and the latest ASGI specifications, staying current with the latest language advancements.
- Added support for `AuthenticationMiddleware` - `BasicAuthMiddleware` to enhance authentication capabilities.

### Changed

- Updated dependencies to ensure compatibility and enhance security, staying vigilant against potential vulnerabilities.
- Included dependencies `Markupsafe` and `Anyio` to leverage their capabilities within the system.

### Fixed

- Resolved minor bugs associated with WebSocket connections, ensuring seamless real-time communication.
- Addressed edge cases in middleware processing to achieve more consistent behavior across different scenarios.
- Fixed issues with URL routing in specific scenarios, improving overall navigation within the application.
- Rectified import errors, ensuring smooth integration with various components.
- Fixed middleware exclusion, preventing unintended interference with specific middleware functions.
- Corrected `CSRF` middleware protection, fortifying against potential security risks.

## [1.12.0] - 2023-12-10

### Added

- Implemented rule and link-based routing, providing a more flexible and intuitive approach to defining application routes.
- Enhanced URL configuration for improved readability and organization.
- Added a diverse range of default middleware support, offering out-of-the-box functionality for common use cases.
- Integrated `__root__` file to centralize management of all apps within the project, improving project structure.
- Introduced `settings` to easily manage AQUILIFY settings, simplifying configuration management.

### Fixed

- Resolved minor bugs associated with WebSocket connections, ensuring seamless real-time communication.
- Addressed edge cases in middleware processing to achieve more consistent behavior across different scenarios.
- Fixed issues with URL routing in specific scenarios, improving overall navigation within the application.
- Rectified import errors, ensuring smooth integration with various components.
- Fixed middleware exclusion, preventing unintended interference with specific middleware functions.
- Corrected `CSRF` middleware protection, fortifying against potential security risks.

### Changes

- Updated dependencies to ensure compatibility and enhance security, staying vigilant against potential vulnerabilities.
- Included dependencies `Markupsafe` and `Anyio` to leverage their capabilities within the system.

## SKIPPED [1.13.0] - 2023-12-10 ...

## [1.14.0] - 2024-01-08

### Added

- Addressed major bug fixes, ensuring a more stable and reliable application.
- Established a clear MVC structure, enhancing code organization and maintainability.
- Added support to interact with the `sqlite3` database, broadening database compatibility.
- Introduced built-in SMTP mailer support, facilitating seamless email integration.
- Added Cache and Singleton messages support, optimizing data storage and retrieval.
- Integrated security middleware to elevate application security, safeguarding against potential threats.
- Provided an extensive range of middleware support, catering to diverse application requirements.
- Added Lifespan and Exception handling through `settings`, enabling fine-tuning of application behavior.
- Implemented a robust request serializer and parser, enhancing data processing capabilities.
- Improved overall application stability, ensuring a reliable user experience.

### Fixed

- Addressed minor bug fixes for enhanced application stability.
- Fixed issues related to the handling of specific middleware scenarios.
- Resolved import errors for improved integration with third-party components.
- Fixed middleware exclusion to prevent unintended interference.

### Changes

- Updated dependencies to guarantee compatibility and enhance security, addressing potential vulnerabilities.
- Included dependencies `Markupsafe` and `Anyio` to capitalize on their capabilities.

## [1.15.0] - 2024-01-22

## Added

- `aquilify.response` - StreamingResponse.
- `excute_from_cmd_line` - AQUILIFY Command line utility

## Fixed

- AQUILIFY `boiler` menu fixed.
- AQUILFY csrf md fixed.
- Improved error handling.
- Improved URL's based routing.
- Improved application speed & concurrency.

## Changes

- Remove dependency from `itsdangerous` and replace with `aquilify.core.signing`
- Remove decorator based exception handling.