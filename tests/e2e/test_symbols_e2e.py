import pytest


@pytest.mark.e2e
class TestSymbolsE2E:
    def test_symbols_total(self, api_client):
        res = api_client.get("/api/symbols_total")
        data = api_client.get_data(res)
        total = data.get("total", data) if isinstance(data, dict) else data
        assert isinstance(total, int)
        assert total >= 0

    def test_symbols_get(self, api_client):
        res = api_client.get("/api/symbols_get", params={"group": "*"})
        data = api_client.get_data(res)
        symbols_list = data if isinstance(data, list) else data.get("symbols", [])
        assert isinstance(symbols_list, list)

    def test_symbol_info(self, api_client, test_symbol):
        res = api_client.get(f"/api/symbol_info/{test_symbol}")
        data = api_client.get_data(res)
        assert "digits" in data or "name" in data or "point" in data

    def test_symbol_select(self, api_client, test_symbol):
        res = api_client.post("/api/symbol_select", data={"symbol": test_symbol, "enable": True})
        data = api_client.get_data(res)
        assert data is not None

    def test_symbol_info_tick(self, api_client, test_symbol):
        res = api_client.get(f"/api/symbol_info_tick/{test_symbol}")
        tick = api_client.get_data(res)
        assert "bid" in tick
        assert "ask" in tick
        assert "time" in tick

    def test_depth_of_market(self, api_client, test_symbol):
        # 1. Subscribe
        sub_res = api_client.post("/api/market_book_add", data={"symbol": test_symbol})
        assert sub_res is not None

        # 2. Query DOM entries
        book_res = api_client.get(f"/api/market_book_get/{test_symbol}")
        book_data = api_client.get_data(book_res)
        assert isinstance(book_data, list)

        # 3. Release subscription
        rel_res = api_client.post("/api/market_book_release", data={"symbol": test_symbol})
        assert rel_res is not None
