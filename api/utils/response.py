from nxcore.controllers.base_controller import (
    response_data,
    response_ok,
    response_error,
)


def make_response(data=None, message=None, error=None, status_code=200):
    """
    Compatibility wrapper delegating to nxcore.controllers.base_controller standard responses.
    """
    if error is not None:
        return response_error(msg=str(error), code=status_code)
    if data is not None:
        return response_data(data, status_code=status_code)
    if message is not None:
        return response_ok(message)
    return response_ok("Success")
