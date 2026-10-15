import pytest


@pytest.mark.e2e
class TestSystemE2E:
    def test_version(self, api_client):
        res = api_client.get("/api/version")
        data = api_client.get_data(res)
        assert "version" in data
        assert "build" in data
        assert "release_date" in data
        assert isinstance(data["version"], int)
        assert isinstance(data["build"], int)

    def test_last_error(self, api_client):
        res = api_client.get("/api/last_error")
        data = api_client.get_data(res)
        assert "code" in data
        assert "description" in data
        assert isinstance(data["code"], int)

    def test_terminal_info(self, api_client):
        res = api_client.get("/api/terminal_info")
        data = api_client.get_data(res)
        assert "connected" in data
        assert "trade_allowed" in data
        assert "company" in data

    def test_account_info(self, api_client):
        res = api_client.get("/api/account_info")
        data = api_client.get_data(res)
        assert "login" in data
        assert "balance" in data
        assert "equity" in data
        assert "currency" in data
        assert "leverage" in data
        assert "server" in data
