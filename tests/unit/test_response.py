import pytest
from flask import Flask

from utils.response import make_response


@pytest.mark.unit
class TestMakeResponse:
    @pytest.fixture
    def app(self):
        return Flask(__name__)

    def test_make_response_data(self, app):
        with app.test_request_context():
            res = make_response(data={"symbol": "EURUSD"}, status_code=200)
            resp, status = res[0], res[1]
            assert status == 200
            json_data = resp.get_json()
            assert json_data.get("symbol") == "EURUSD" or json_data.get("data") == {"symbol": "EURUSD"}

    def test_make_response_message(self, app):
        with app.test_request_context():
            res = make_response(message="Operation successful")
            resp = res[0] if isinstance(res, tuple) else res
            json_data = resp.get_json()
            msg = json_data.get("message", "")
            assert "success" in msg.lower() or "successful" in msg.lower()

    def test_make_response_error(self, app):
        with app.test_request_context():
            res = make_response(error="Invalid parameters", status_code=400)
            resp, status = res[0], res[1]
            assert status == 400
            json_data = resp.get_json()
            assert "Invalid parameters" in json_data.get("message", "")

    def test_make_response_default(self, app):
        with app.test_request_context():
            res = make_response()
            resp = res[0] if isinstance(res, tuple) else res
            json_data = resp.get_json()
            assert "success" in json_data.get("message", "").lower()
