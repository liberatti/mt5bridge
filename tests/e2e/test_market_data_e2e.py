from datetime import datetime, timedelta, timezone
import pytest


@pytest.mark.e2e
class TestMarketDataE2E:
    def test_copy_rates_from_pos(self, api_client, test_symbol):
        res = api_client.get(
            "/api/copy_rates_from_pos",
            params={"symbol": test_symbol, "timeframe": "M1", "start_pos": 0, "count": 5},
        )
        data = api_client.get_data(res)
        rates = data.get("rates", data) if isinstance(data, dict) else data
        assert isinstance(rates, list)

    def test_copy_rates_from(self, api_client, test_symbol):
        past_date = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/copy_rates_from",
            params={"symbol": test_symbol, "timeframe": "M1", "date_from": past_date, "count": 5},
        )
        data = api_client.get_data(res)
        rates = data.get("rates", data) if isinstance(data, dict) else data
        assert isinstance(rates, list)

    def test_copy_rates_range(self, api_client, test_symbol):
        dt_start = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        dt_end = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/copy_rates_range",
            params={"symbol": test_symbol, "timeframe": "M1", "date_from": dt_start, "date_to": dt_end},
        )
        data = api_client.get_data(res)
        rates = data.get("rates", data) if isinstance(data, dict) else data
        assert isinstance(rates, list)

    def test_copy_ticks_from(self, api_client, test_symbol):
        past_date = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/copy_ticks_from",
            params={"symbol": test_symbol, "date_from": past_date, "count": 10, "flags": "ALL"},
        )
        data = api_client.get_data(res)
        ticks = data.get("ticks", data) if isinstance(data, dict) else data
        assert isinstance(ticks, list)

    def test_copy_ticks_range(self, api_client, test_symbol):
        dt_start = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        dt_end = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/copy_ticks_range",
            params={"symbol": test_symbol, "date_from": dt_start, "date_to": dt_end, "flags": "ALL"},
        )
        data = api_client.get_data(res)
        ticks = data.get("ticks", data) if isinstance(data, dict) else data
        assert isinstance(ticks, list)
