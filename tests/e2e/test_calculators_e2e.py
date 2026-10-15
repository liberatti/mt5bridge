import pytest


@pytest.mark.e2e
class TestCalculatorsE2E:
    def test_order_calc_margin(self, api_client, test_symbol, test_volume):
        tick_res = api_client.get(f"/api/symbol_info_tick/{test_symbol}")
        tick = api_client.get_data(tick_res)
        ask_price = float(tick.get("ask", 1.15))
        bid_price = float(tick.get("bid", 1.15))

        # Margin BUY
        buy_res = api_client.post(
            "/api/order_calc_margin",
            data={"action": 0, "symbol": test_symbol, "volume": test_volume, "price": ask_price},
        )
        buy_data = api_client.get_data(buy_res)
        assert "margin" in buy_data

        # Margin SELL
        sell_res = api_client.post(
            "/api/order_calc_margin",
            data={"action": 1, "symbol": test_symbol, "volume": test_volume, "price": bid_price},
        )
        sell_data = api_client.get_data(sell_res)
        assert "margin" in sell_data

    def test_order_calc_profit(self, api_client, test_symbol, test_volume):
        tick_res = api_client.get(f"/api/symbol_info_tick/{test_symbol}")
        tick = api_client.get_data(tick_res)
        ask_price = float(tick.get("ask", 1.15))
        bid_price = float(tick.get("bid", 1.15))

        # Profit BUY
        buy_res = api_client.post(
            "/api/order_calc_profit",
            data={
                "action": 0,
                "symbol": test_symbol,
                "volume": test_volume,
                "price_open": ask_price,
                "price_close": round(ask_price + 0.0050, 5),
            },
        )
        buy_data = api_client.get_data(buy_res)
        assert "profit" in buy_data

        # Profit SELL
        sell_res = api_client.post(
            "/api/order_calc_profit",
            data={
                "action": 1,
                "symbol": test_symbol,
                "volume": test_volume,
                "price_open": bid_price,
                "price_close": round(bid_price - 0.0050, 5),
            },
        )
        sell_data = api_client.get_data(sell_res)
        assert "profit" in sell_data

    def test_order_check(self, api_client, test_symbol, test_volume):
        tick_res = api_client.get(f"/api/symbol_info_tick/{test_symbol}")
        tick = api_client.get_data(tick_res)
        ask_price = float(tick.get("ask", 1.15))

        check_payload = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": test_symbol,
            "volume": test_volume,
            "type": 0,    # BUY
            "price": ask_price,
            "deviation": 20,
        }
        res = api_client.post("/api/order_check", data=check_payload)
        chk_data = api_client.get_data(res)
        assert "retcode" in chk_data
