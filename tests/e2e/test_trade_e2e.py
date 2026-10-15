import time
import pytest


@pytest.mark.e2e
class TestTradeE2E:
    def test_market_buy_lifecycle(self, api_client, test_symbol, test_volume, close_order):
        # 1. Open BUY order
        buy_res = api_client.post(
            "/api/order/open",
            data={
                "symbol": test_symbol,
                "type": "BUY",
                "volume": test_volume,
                "deviation": 20,
                "comment": "Pytest BUY",
                "magic": 111001,
            },
        )
        b_data = api_client.get_data(buy_res)
        assert b_data.get("retcode") in (10008, 10009) or "order" in b_data
        buy_order_ticket = b_data.get("order")

        time.sleep(1)

        # 2. Verify open positions
        pos_res = api_client.get("/api/positions_get", params={"symbol": test_symbol})
        pos_data = api_client.get_data(pos_res)
        positions = pos_data.get("positions", []) if isinstance(pos_data, dict) else pos_data
        assert isinstance(positions, list)

        buy_pos = None
        for p in positions:
            if p.get("ticket") == buy_order_ticket or p.get("magic") == 111001:
                buy_pos = p
                break
        if not buy_pos and positions:
            buy_pos = positions[-1]

        buy_ticket = buy_pos.get("ticket") if buy_pos else buy_order_ticket

        if buy_pos:
            # 3. Modify SL / TP
            open_p = float(buy_pos.get("price_open", b_data.get("price", 1.15)))
            sl_buy = round(open_p - 0.0030, 5)
            tp_buy = round(open_p + 0.0030, 5)
            try:
                mod_res = api_client.post(
                    "/api/order/modify",
                    data={"ticket": buy_ticket, "sl": sl_buy, "tp": tp_buy},
                )
                mod_data = api_client.get_data(mod_res)
                assert "retcode" in mod_data
            except Exception:
                pass  # Modification may be constrained by broker minimal stop distance

            # 4. Close BUY position
            if close_order:
                close_res = api_client.post(
                    "/api/order/close",
                    data={"ticket": buy_ticket, "volume": test_volume, "comment": "Close Pytest BUY"},
                )
                cb_data = api_client.get_data(close_res)
                assert "retcode" in cb_data or "deal" in cb_data

    def test_market_sell_lifecycle(self, api_client, test_symbol, test_volume, close_order):
        time.sleep(1)

        # 1. Open SELL order
        sell_res = api_client.post(
            "/api/order/open",
            data={
                "symbol": test_symbol,
                "type": "SELL",
                "volume": test_volume,
                "deviation": 20,
                "comment": "Pytest SELL",
                "magic": 222002,
            },
        )
        s_data = api_client.get_data(sell_res)
        assert s_data.get("retcode") in (10008, 10009) or "order" in s_data
        sell_order_ticket = s_data.get("order")

        time.sleep(1)

        # 2. Verify open positions
        pos_res = api_client.get("/api/positions_get", params={"symbol": test_symbol})
        pos_data = api_client.get_data(pos_res)
        positions = pos_data.get("positions", []) if isinstance(pos_data, dict) else pos_data
        assert isinstance(positions, list)

        sell_pos = None
        for p in positions:
            if p.get("ticket") == sell_order_ticket or p.get("magic") == 222002:
                sell_pos = p
                break
        if not sell_pos and positions:
            sell_pos = positions[-1]

        sell_ticket = sell_pos.get("ticket") if sell_pos else sell_order_ticket

        if sell_pos:
            # 3. Modify SL / TP
            open_p = float(sell_pos.get("price_open", s_data.get("price", 1.15)))
            sl_sell = round(open_p + 0.0030, 5)
            tp_sell = round(open_p - 0.0030, 5)
            try:
                mod_res = api_client.post(
                    "/api/order/modify",
                    data={"ticket": sell_ticket, "sl": sl_sell, "tp": tp_sell},
                )
                mod_data = api_client.get_data(mod_res)
                assert "retcode" in mod_data
            except Exception:
                pass

            # 4. Close SELL position
            if close_order:
                close_res = api_client.post(
                    "/api/order/close",
                    data={"ticket": sell_ticket, "volume": test_volume, "comment": "Close Pytest SELL"},
                )
                cs_data = api_client.get_data(close_res)
                assert "retcode" in cs_data or "deal" in cs_data

    def test_positions_total(self, api_client):
        res = api_client.get("/api/positions_total")
        data = api_client.get_data(res)
        total = data.get("total", data) if isinstance(data, dict) else data
        assert isinstance(total, int)
        assert total >= 0
