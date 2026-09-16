from nxcore.controllers.base_controller import (
    response_data,
    response_data_list,
    response_ok,
    response_error,
    response_error_404,
    response_error_401,
    response_error_403,
    response_error_500,
    response_error_parse,
    get_pagination,
    has_any_authority,
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

