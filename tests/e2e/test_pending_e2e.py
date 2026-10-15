import time
import pytest


@pytest.mark.e2e
class TestPendingOrdersE2E:
    def test_pending_orders_lifecycle(self, api_client, test_symbol, test_volume):
        tick_res = api_client.get(f"/api/symbol_info_tick/{test_symbol}")
        tick = api_client.get_data(tick_res)
        bid = float(tick.get("bid", 1.15))
        limit_price = round(bid - 0.0100, 5)

        # 1. Place BUY_LIMIT
        pending_payload = {
            "action": 5,  # TRADE_ACTION_PENDING
            "symbol": test_symbol,
            "volume": test_volume,
            "type": 2,    # ORDER_TYPE_BUY_LIMIT
            "price": limit_price,
            "comment": "Pytest BUY_LIMIT",
            "magic": 333003,
        }
        pend_res = api_client.post("/api/order_send", data=pending_payload)
        p_data = api_client.get_data(pend_res)
        assert "retcode" in p_data or "order" in p_data
        pending_ticket = p_data.get("order")

        time.sleep(1)

        # 2. Query pending orders list
        orders_res = api_client.get("/api/orders_get", params={"symbol": test_symbol})
        orders_data = api_client.get_data(orders_res)
        orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data
        assert isinstance(orders, list)

        # 3. Query total pending orders
        tot_res = api_client.get("/api/orders_total")
        total = api_client.get_data(tot_res)
        assert isinstance(total, int) or "total" in total

        # 4. Cancel Pending Order
        if pending_ticket:
            cancel_res = api_client.delete(f"/api/order/{pending_ticket}")
            c_data = api_client.get_data(cancel_res)
            assert "retcode" in c_data or c_data is not None
