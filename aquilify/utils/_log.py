import logging

request_logger = logging.getLogger("aquilify.request")

def log_response(
    message,
    *args,
    response=None,
    request=None,
    logger=request_logger,
    level=None,
    exception=None,
):
    if getattr(response, "_has_been_logged", False):
        return

    if level is None:
        if response.status_code >= 500:
            level = "error"
        elif response.status_code >= 400:
            level = "warning"
        else:
            level = "info"

    getattr(logger, level)(
        message,
        *args,
        extra={
            "status_code": response.status_code,
            "request": request,
        },
        exc_info=exception,
    )
    response._has_been_logged = True