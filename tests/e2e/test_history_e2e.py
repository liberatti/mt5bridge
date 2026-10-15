from datetime import datetime, timedelta, timezone
import pytest


@pytest.mark.e2e
class TestHistoryE2E:
    def test_history_orders_total(self, api_client):
        dt_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        dt_to = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get("/api/history_orders_total", params={"date_from": dt_from, "date_to": dt_to})
        total = api_client.get_data(res)
        assert isinstance(total, int) or "total" in total

    def test_history_orders_get(self, api_client, test_symbol):
        dt_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        dt_to = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/history_orders_get",
            params={"date_from": dt_from, "date_to": dt_to, "group": f"*{test_symbol}*"},
        )
        data = api_client.get_data(res)
        orders = data.get("orders", data) if isinstance(data, dict) else data
        assert isinstance(orders, list)

    def test_history_deals_total(self, api_client):
        dt_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        dt_to = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get("/api/history_deals_total", params={"date_from": dt_from, "date_to": dt_to})
        total = api_client.get_data(res)
        assert isinstance(total, int) or "total" in total

    def test_history_deals_get(self, api_client, test_symbol):
        dt_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        dt_to = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        res = api_client.get(
            "/api/history_deals_get",
            params={"date_from": dt_from, "date_to": dt_to, "group": f"*{test_symbol}*"},
        )
        data = api_client.get_data(res)
        deals = data.get("deals", data) if isinstance(data, dict) else data
        assert isinstance(deals, list)
