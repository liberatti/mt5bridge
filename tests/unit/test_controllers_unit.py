import pytest
from unittest.mock import patch

import config
from app import create_app


def get_data(res_json, key=None):
    if isinstance(res_json, dict):
        val = res_json.get("data", res_json)
        if key and isinstance(val, dict):
            return val.get(key, val)
        return val
    return res_json


@pytest.fixture
def app():
    config.SECURITY_ENABLED = False
    application = create_app()
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.mark.unit
class TestDocumentationRoutes:
    def test_index_html(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"html" in resp.data.lower() or b"swagger" in resp.data.lower()

    def test_index_json_query(self, client):
        resp = client.get("/?format=json")
        assert resp.status_code == 200
        assert resp.is_json
        data = resp.get_json()
        assert "openapi" in data or "swagger" in data or "info" in data

    def test_index_json_header(self, client):
        resp = client.get("/", headers={"Accept": "application/json"})
        assert resp.status_code == 200
        assert resp.is_json

    def test_swagger_json(self, client):
        resp = client.get("/swagger.json")
        assert resp.status_code == 200
        assert resp.is_json

    def test_branding_assets(self, client):
        resp_logo = client.get("/logo.svg")
        assert resp_logo.status_code == 200
        resp_icon = client.get("/icon.svg")
        assert resp_icon.status_code == 200
        resp_fav = client.get("/favicon.ico")
        assert resp_fav.status_code in (200, 204)

    def test_not_found_route(self, client):
        resp = client.get("/api/non_existent_endpoint")
        assert resp.status_code == 404


@pytest.mark.unit
class TestSystemControllerUnit:
    @patch("controllers.system_controller.service")
    def test_api_version(self, mock_service, client):
        mock_service.version.return_value = {
            "version": 500,
            "build": 4150,
            "release_date": "10 Dec 2024",
        }
        resp = client.get("/api/version")
        assert resp.status_code == 200
        data = get_data(resp.get_json())
        assert data.get("build") == 4150

    @patch("controllers.system_controller.service")
    def test_api_last_error(self, mock_service, client):
        mock_service.last_error.return_value = {"code": 1, "description": "Success"}
        resp = client.get("/api/last_error")
        assert resp.status_code == 200
        data = get_data(resp.get_json())
        assert data.get("code") == 1

    @patch("controllers.system_controller.service")
    def test_api_terminal_info(self, mock_service, client):
        mock_service.terminal_info.return_value = {
            "connected": True,
            "trade_allowed": True,
            "company": "MetaQuotes Software Corp.",
        }
        resp = client.get("/api/terminal_info")
        assert resp.status_code == 200
        data = get_data(resp.get_json())
        assert data.get("connected") is True

    @patch("controllers.system_controller.service")
    def test_api_account_info(self, mock_service, client):
        mock_service.account_info.return_value = {
            "login": 123456,
            "balance": 10000.0,
            "equity": 10000.0,
            "currency": "USD",
            "leverage": 100,
        }
        resp = client.get("/api/account_info")
        assert resp.status_code == 200
        data = get_data(resp.get_json())
        assert data.get("login") == 123456

    def test_login_missing_fields(self, client):
        resp = client.post("/api/login", json={"login": 123456})
        assert resp.status_code == 400
        json_data = resp.get_json()
        assert "Missing required fields" in json_data.get("message", "")

    def test_login_invalid_login_type(self, client):
        resp = client.post(
            "/api/login",
            json={"login": "invalid_login", "password": "pwd", "server": "srv"},
        )
        assert resp.status_code == 400
        json_data = resp.get_json()
        assert "must be a valid integer" in json_data.get("message", "")

    @patch("controllers.system_controller.service")
    def test_login_success(self, mock_service, client):
        mock_service.login.return_value = {"login": 123456, "server": "DemoServer"}
        resp = client.post(
            "/api/login",
            json={"login": 123456, "password": "pwd", "server": "DemoServer"},
        )
        assert resp.status_code == 200
        data = get_data(resp.get_json())
        assert data.get("login") == 123456
