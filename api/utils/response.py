from flask import jsonify

def make_response(data=None, message=None, error=None, status_code=200):
    payload = {
        "success": error is None,
    }
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if error is not None:
        payload["error"] = str(error)
    return jsonify(payload), status_code
