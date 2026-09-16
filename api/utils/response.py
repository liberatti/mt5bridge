from typing import Any, Optional
from flask import Response
from nxcore.controllers.base_controller import (
    response_data,
    response_ok,
    response_error,
)


def make_response(
    data: Optional[Any] = None,
    message: Optional[str] = None,
    error: Optional[Any] = None,
    status_code: int = 200,
) -> Response:
    """
    Compatibility response wrapper delegating to nxcore standardized response format.

    Args:
        data (Any, optional): Data payload to return inside the response.
        message (str, optional): Success/status message.
        error (Any, optional): Error message or exception object.
        status_code (int, optional): HTTP status code. Defaults to 200.

    Returns:
        Response: Flask JSON response object.
    """
    if error is not None:
        return response_error(msg=str(error), code=status_code)
    if data is not None:
        return response_data(data, status_code=status_code)
    if message is not None:
        return response_ok(message)
    return response_ok("Success")

