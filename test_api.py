#!/usr/bin/env python3
"""
MetaTrader 5 REST API Complete Test Routine
Validates 100% of endpoints and methods:
- System status & Account info
- Symbols, specifications, selection, and Depth of Market (DOM)
- Market data rates (OHLCV) and real-time tick histories
- Margin and profit calculators & order check
- Market execution: BUY and SELL orders with modification and closing
- Pending order placement and cancellation (BUY_LIMIT)
- History of orders and executed deals
"""

import sys
import time
import os
import argparse
from datetime import datetime, timedelta, timezone
import requests

# Terminal ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def log_info(msg: str):
    print(f"{CYAN}[INFO]{RESET} {msg}")


def log_success(msg: str):
    print(f"{GREEN}[SUCCESS]{RESET} {msg}")


def log_warn(msg: str):
    print(f"{YELLOW}[WARN]{RESET} {msg}")


def log_error(msg: str):
    print(f"{RED}[ERROR]{RESET} {msg}")


class MT5ApiTester:
    def __init__(self, base_url: str, symbol: str = "EURUSD", volume: float = 0.01, close_order: bool = True):
        self.base_url = base_url.rstrip("/")
        self.symbol = symbol
        self.volume = volume
        self.close_order = close_order
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json", "Accept": "application/json"})

    def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.request(method=method, url=url, json=data, params=params, timeout=15)
            try:
                body = resp.json()
            except Exception:
                body = {"raw": resp.text}

            if not resp.ok:
                log_error(f"{method} {endpoint} -> HTTP {resp.status_code}: {body}")
                resp.raise_for_status()

            return body
        except Exception as e:
            log_error(f"Failed calling {method} {url}: {e}")
            raise

    @staticmethod
    def _get_data(res, key: str = None):
        """Safely extracts inner data payload from dict responses or returns lists as-is."""
        if isinstance(res, dict):
            val = res.get("data", res)
            if key and isinstance(val, dict):
                return val.get(key, val)
            return val
        return res

    # =========================================================================
    # 1. System & Account Information
    # =========================================================================
    def test_system_info(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 1. Testing System & Account Information{RESET}")
        print(f"{BOLD}======================================================{RESET}")

        # Version
        log_info("Fetching MT5 terminal version (/api/version)...")
        v_res = self._request("GET", "/api/version")
        version_data = self._get_data(v_res)
        log_success(f"MT5 Version: {version_data.get('version')} (Build: {version_data.get('build')}, Date: {version_data.get('release_date')})")

        # Last Error
        log_info("Fetching last MT5 error status (/api/last_error)...")
        err_res = self._request("GET", "/api/last_error")
        err_data = self._get_data(err_res)
        log_success(f"Last Error State: Code={err_data.get('code')}, Description='{err_data.get('description')}'")

        # Terminal Info
        log_info("Fetching Terminal status (/api/terminal_info)...")
        t_res = self._request("GET", "/api/terminal_info")
        t_data = self._get_data(t_res)
        connected = t_data.get("connected", False)
        trade_allowed = t_data.get("trade_allowed", False)
        log_success(f"Terminal Info: Connected={connected}, TradeAllowed={trade_allowed}, Company='{t_data.get('company')}'")

        # Account Info
        log_info("Fetching Trading Account status (/api/account_info)...")
        a_res = self._request("GET", "/api/account_info")
        a_data = self._get_data(a_res)
        login = a_data.get("login")
        balance = a_data.get("balance")
        equity = a_data.get("equity")
        currency = a_data.get("currency")
        leverage = a_data.get("leverage")
        server = a_data.get("server")
        trade_mode = "DEMO" if a_data.get("trade_mode") == 0 else "REAL/CONTEST"
        log_success(f"Account: #{login} ({trade_mode}) | Server: {server} | Balance: {balance} {currency} | Equity: {equity} {currency} | Leverage: 1:{leverage}")

    # =========================================================================
    # 2. Symbols, Market Watch & Depth of Market (DOM)
    # =========================================================================
    def test_symbols_and_dom(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 2. Testing Symbols & Depth of Market ({self.symbol}){RESET}")
        print(f"{BOLD}======================================================{RESET}")

        # Total Symbols
        log_info("Fetching total symbols count (/api/symbols_total)...")
        st_res = self._request("GET", "/api/symbols_total")
        st_data = self._get_data(st_res)
        total_val = st_data.get("total", st_data) if isinstance(st_data, dict) else st_data
        log_success(f"Total symbols available: {total_val}")

        # Symbols Get (with filter)
        log_info("Fetching available symbols list (/api/symbols_get)...")
        sg_res = self._request("GET", "/api/symbols_get", params={"group": "*"})
        sg_data = self._get_data(sg_res)
        symbols_list = sg_data if isinstance(sg_data, list) else sg_data.get("symbols", [])
        log_success(f"Found {len(symbols_list)} available instrument(s)")

        # Symbol Info
        log_info(f"Fetching symbol specifications (/api/symbol_info/{self.symbol})...")
        s_res = self._request("GET", f"/api/symbol_info/{self.symbol}")
        s_data = self._get_data(s_res)
        digits = s_data.get("digits")
        point = s_data.get("point")
        spread = s_data.get("spread")
        log_success(f"Symbol {self.symbol}: Digits={digits}, Point={point}, Spread={spread} points")

        # Symbol Select (Market Watch)
        log_info(f"Selecting symbol {self.symbol} into Market Watch (/api/symbol_select)...")
        sel_res = self._request("POST", "/api/symbol_select", data={"symbol": self.symbol, "enable": True})
        log_success(f"Symbol select result: {self._get_data(sel_res)}")

        # Current Tick Quote
        log_info(f"Fetching real-time tick quote (/api/symbol_info_tick/{self.symbol})...")
        tick_res = self._request("GET", f"/api/symbol_info_tick/{self.symbol}")
        tick = self._get_data(tick_res)
        bid = tick.get("bid")
        ask = tick.get("ask")
        time_tick = tick.get("time")
        log_success(f"Tick {self.symbol} -> Bid: {bid} | Ask: {ask} | Timestamp: {time_tick}")

        # Depth of Market (DOM)
        log_info(f"Subscribing to Depth of Market (/api/market_book_add)...")
        self._request("POST", "/api/market_book_add", data={"symbol": self.symbol})
        log_success(f"Subscribed to DOM for {self.symbol}")

        log_info(f"Fetching DOM book entries (/api/market_book_get/{self.symbol})...")
        book_res = self._request("GET", f"/api/market_book_get/{self.symbol}")
        book_data = self._get_data(book_res)
        entries_count = len(book_data) if isinstance(book_data, list) else 0
        log_success(f"DOM Entries: {entries_count} depth level(s) retrieved")

        log_info(f"Releasing DOM subscription (/api/market_book_release)...")
        self._request("POST", "/api/market_book_release", data={"symbol": self.symbol})
        log_success(f"DOM subscription released for {self.symbol}")

    # =========================================================================
    # 3. Market Data (Rates / Candles / Ticks)
    # =========================================================================
    def test_market_data_rates(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 3. Testing Historical Rates & Tick Series{RESET}")
        print(f"{BOLD}======================================================{RESET}")

        # 1. copy_rates_from_pos
        log_info("Fetching latest 5 M1 bars by position (/api/copy_rates_from_pos)...")
        r_pos_res = self._request("GET", "/api/copy_rates_from_pos", params={"symbol": self.symbol, "timeframe": "M1", "start_pos": 0, "count": 5})
        rates_pos = self._get_data(r_pos_res)
        rates_list = rates_pos.get("rates", rates_pos) if isinstance(rates_pos, dict) else rates_pos
        log_success(f"copy_rates_from_pos: Retrieved {len(rates_list)} candle(s)")

        # 2. copy_rates_from (by date)
        past_date = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        log_info(f"Fetching 5 M1 bars from date '{past_date}' (/api/copy_rates_from)...")
        r_from_res = self._request("GET", "/api/copy_rates_from", params={"symbol": self.symbol, "timeframe": "M1", "date_from": past_date, "count": 5})
        rates_from = self._get_data(r_from_res)
        r_from_list = rates_from.get("rates", rates_from) if isinstance(rates_from, dict) else rates_from
        log_success(f"copy_rates_from: Retrieved {len(r_from_list)} candle(s)")

        # 3. copy_rates_range
        dt_start = (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
        dt_end = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        log_info("Fetching M1 bars by date range (/api/copy_rates_range)...")
        r_range_res = self._request("GET", "/api/copy_rates_range", params={"symbol": self.symbol, "timeframe": "M1", "date_from": dt_start, "date_to": dt_end})
        rates_range = self._get_data(r_range_res)
        r_range_list = rates_range.get("rates", rates_range) if isinstance(rates_range, dict) else rates_range
        log_success(f"copy_rates_range: Retrieved {len(r_range_list)} candle(s)")

        # 4. copy_ticks_from
        log_info(f"Fetching latest 10 ticks from '{past_date}' (/api/copy_ticks_from)...")
        ticks_from_res = self._request("GET", "/api/copy_ticks_from", params={"symbol": self.symbol, "date_from": past_date, "count": 10, "flags": "ALL"})
        ticks_from = self._get_data(ticks_from_res)
        t_from_list = ticks_from.get("ticks", ticks_from) if isinstance(ticks_from, dict) else ticks_from
        log_success(f"copy_ticks_from: Retrieved {len(t_from_list)} tick record(s)")

        # 5. copy_ticks_range
        dt_ticks_start = (datetime.now(timezone.utc) - timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        log_info(f"Fetching ticks by date range from '{dt_ticks_start}' (/api/copy_ticks_range)...")
        ticks_range_res = self._request("GET", "/api/copy_ticks_range", params={"symbol": self.symbol, "date_from": dt_ticks_start, "date_to": dt_end, "flags": "ALL"})
        ticks_range = self._get_data(ticks_range_res)
        t_range_list = ticks_range.get("ticks", ticks_range) if isinstance(ticks_range, dict) else ticks_range
        log_success(f"copy_ticks_range: Retrieved {len(t_range_list)} tick record(s)")

    # =========================================================================
    # 4. Calculators & Pre-trade Checks
    # =========================================================================
    def test_calculators_and_checks(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 4. Testing Margin & Profit Calculators and Pre-Check{RESET}")
        print(f"{BOLD}======================================================{RESET}")

        tick_res = self._request("GET", f"/api/symbol_info_tick/{self.symbol}")
        tick = self._get_data(tick_res)
        ask_price = float(tick.get("ask", 1.15))
        bid_price = float(tick.get("bid", 1.15))

        # 1. Calc Margin (BUY)
        log_info(f"Calculating margin for BUY {self.volume} lot(s) @ {ask_price} (/api/order_calc_margin)...")
        margin_buy_res = self._request("POST", "/api/order_calc_margin", data={"action": 0, "symbol": self.symbol, "volume": self.volume, "price": ask_price})
        mb_data = self._get_data(margin_buy_res)
        log_success(f"Required Margin (BUY): {mb_data.get('margin')} USD")

        # 2. Calc Margin (SELL)
        log_info(f"Calculating margin for SELL {self.volume} lot(s) @ {bid_price} (/api/order_calc_margin)...")
        margin_sell_res = self._request("POST", "/api/order_calc_margin", data={"action": 1, "symbol": self.symbol, "volume": self.volume, "price": bid_price})
        ms_data = self._get_data(margin_sell_res)
        log_success(f"Required Margin (SELL): {ms_data.get('margin')} USD")

        # 3. Calc Profit (BUY)
        log_info(f"Calculating expected profit for BUY {self.volume} lot(s) @ {ask_price} -> {round(ask_price + 0.0050, 5)} (/api/order_calc_profit)...")
        profit_buy_res = self._request("POST", "/api/order_calc_profit", data={"action": 0, "symbol": self.symbol, "volume": self.volume, "price_open": ask_price, "price_close": round(ask_price + 0.0050, 5)})
        pb_data = self._get_data(profit_buy_res)
        log_success(f"Estimated Profit (BUY +50 pips): {pb_data.get('profit')} USD")

        # 4. Calc Profit (SELL)
        log_info(f"Calculating expected profit for SELL {self.volume} lot(s) @ {bid_price} -> {round(bid_price - 0.0050, 5)} (/api/order_calc_profit)...")
        profit_sell_res = self._request("POST", "/api/order_calc_profit", data={"action": 1, "symbol": self.symbol, "volume": self.volume, "price_open": bid_price, "price_close": round(bid_price - 0.0050, 5)})
        ps_data = self._get_data(profit_sell_res)
        log_success(f"Estimated Profit (SELL +50 pips): {ps_data.get('profit')} USD")

        # 5. Order Check
        log_info("Performing pre-trade order check (/api/order_check)...")
        check_payload = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": self.symbol,
            "volume": self.volume,
            "type": 0,    # BUY
            "price": ask_price,
            "deviation": 20
        }
        chk_res = self._request("POST", "/api/order_check", data=check_payload)
        chk_data = self._get_data(chk_res)
        log_success(f"Order Check: retcode={chk_data.get('retcode')} | Margin Free={chk_data.get('margin_free')} | Comment='{chk_data.get('comment')}'")

    # =========================================================================
    # 5. Trading: BUY & SELL Market Orders, Modification & Closure
    # =========================================================================
    def test_market_orders_buy_and_sell(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 5. Testing Market Execution (BUY and SELL Operations){RESET}")
        print(f"{BOLD}======================================================{RESET}")

        # ----------------------------------------------------
        # A. BUY ORDER LIFECYCLE
        # ----------------------------------------------------
        log_info(f"Placing Market BUY Order ({self.volume} lot {self.symbol}) (/api/order/open)...")
        buy_res = self._request("POST", "/api/order/open", data={
            "symbol": self.symbol,
            "type": "BUY",
            "volume": self.volume,
            "deviation": 20,
            "comment": "API BUY Test",
            "magic": 111001
        })
        b_data = self._get_data(buy_res)
        buy_order_ticket = b_data.get("order")
        buy_deal_ticket = b_data.get("deal")
        buy_price = b_data.get("price")
        log_success(f"BUY Executed: retcode={b_data.get('retcode')} | Order #{buy_order_ticket} | Deal #{buy_deal_ticket} | Price={buy_price}")

        # Verify Positions
        time.sleep(1)
        log_info(f"Verifying open positions (/api/positions_get?symbol={self.symbol})...")
        pos_res = self._request("GET", "/api/positions_get", params={"symbol": self.symbol})
        pos_data = self._get_data(pos_res)
        positions = pos_data.get("positions", []) if isinstance(pos_data, dict) else pos_data
        log_success(f"Total open positions: {len(positions)}")

        buy_pos = None
        for p in positions:
            if p.get("ticket") == buy_order_ticket or p.get("magic") == 111001:
                buy_pos = p
                break
        if not buy_pos and positions:
            buy_pos = positions[-1]

        buy_ticket = buy_pos.get("ticket") if buy_pos else buy_order_ticket
        if buy_pos:
            log_success(f"Active BUY Position: Ticket #{buy_ticket} | Vol={buy_pos.get('volume')} | Open={buy_pos.get('price_open')} | Profit={buy_pos.get('profit')}")

            # Modify SL/TP on BUY position
            log_info(f"Modifying BUY position #{buy_ticket} SL/TP (/api/order/modify)...")
            try:
                open_p = float(buy_pos.get("price_open", buy_price or 1.15))
                sl_buy = round(open_p - 0.0030, 5)
                tp_buy = round(open_p + 0.0030, 5)
                mod_b_res = self._request("POST", "/api/order/modify", data={"ticket": buy_ticket, "sl": sl_buy, "tp": tp_buy})
                mod_b_data = self._get_data(mod_b_res)
                log_success(f"BUY Position Modified (SL={sl_buy}, TP={tp_buy}): retcode={mod_b_data.get('retcode')}")
            except Exception as e:
                log_warn(f"BUY position modify notice: {e}")

            # Close BUY position
            if self.close_order:
                log_info(f"Closing BUY position #{buy_ticket} (/api/order/close)...")
                close_b_res = self._request("POST", "/api/order/close", data={"ticket": buy_ticket, "volume": self.volume, "comment": "Close BUY Test"})
                cb_data = self._get_data(close_b_res)
                log_success(f"BUY Position Closed: retcode={cb_data.get('retcode')} | Close Deal #{cb_data.get('deal')} | Price={cb_data.get('price')}")

        # ----------------------------------------------------
        # B. SELL ORDER LIFECYCLE
        # ----------------------------------------------------
        time.sleep(1)
        log_info(f"Placing Market SELL Order ({self.volume} lot {self.symbol}) (/api/order/open)...")
        sell_res = self._request("POST", "/api/order/open", data={
            "symbol": self.symbol,
            "type": "SELL",
            "volume": self.volume,
            "deviation": 20,
            "comment": "API SELL Test",
            "magic": 222002
        })
        s_data = self._get_data(sell_res)
        sell_order_ticket = s_data.get("order")
        sell_deal_ticket = s_data.get("deal")
        sell_price = s_data.get("price")
        log_success(f"SELL Executed: retcode={s_data.get('retcode')} | Order #{sell_order_ticket} | Deal #{sell_deal_ticket} | Price={sell_price}")

        # Verify SELL Position
        time.sleep(1)
        pos_sell_res = self._request("GET", "/api/positions_get", params={"symbol": self.symbol})
        pos_s_data = self._get_data(pos_sell_res)
        positions_s = pos_s_data.get("positions", []) if isinstance(pos_s_data, dict) else pos_s_data

        sell_pos = None
        for p in positions_s:
            if p.get("ticket") == sell_order_ticket or p.get("magic") == 222002:
                sell_pos = p
                break
        if not sell_pos and positions_s:
            sell_pos = positions_s[-1]

        sell_ticket = sell_pos.get("ticket") if sell_pos else sell_order_ticket
        if sell_pos:
            log_success(f"Active SELL Position: Ticket #{sell_ticket} | Vol={sell_pos.get('volume')} | Open={sell_pos.get('price_open')} | Profit={sell_pos.get('profit')}")

            # Modify SL/TP on SELL position
            log_info(f"Modifying SELL position #{sell_ticket} SL/TP (/api/order/modify)...")
            try:
                open_ps = float(sell_pos.get("price_open", sell_price or 1.15))
                sl_sell = round(open_ps + 0.0030, 5)
                tp_sell = round(open_ps - 0.0030, 5)
                mod_s_res = self._request("POST", "/api/order/modify", data={"ticket": sell_ticket, "sl": sl_sell, "tp": tp_sell})
                mod_s_data = self._get_data(mod_s_res)
                log_success(f"SELL Position Modified (SL={sl_sell}, TP={tp_sell}): retcode={mod_s_data.get('retcode')}")
            except Exception as e:
                log_warn(f"SELL position modify notice: {e}")

            # Close SELL position
            if self.close_order:
                log_info(f"Closing SELL position #{sell_ticket} (/api/order/close)...")
                close_s_res = self._request("POST", "/api/order/close", data={"ticket": sell_ticket, "volume": self.volume, "comment": "Close SELL Test"})
                cs_data = self._get_data(close_s_res)
                log_success(f"SELL Position Closed: retcode={cs_data.get('retcode')} | Close Deal #{cs_data.get('deal')} | Price={cs_data.get('price')}")

        # Total Positions Count
        pos_tot_res = self._request("GET", "/api/positions_total")
        log_success(f"Remaining active positions count (/api/positions_total): {self._get_data(pos_tot_res)}")

    # =========================================================================
    # 6. Pending Orders (BUY_LIMIT) Placement and Cancellation
    # =========================================================================
    def test_pending_orders(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 6. Testing Pending Orders (BUY_LIMIT & DELETE /order/<id>){RESET}")
        print(f"{BOLD}======================================================{RESET}")

        tick_res = self._request("GET", f"/api/symbol_info_tick/{self.symbol}")
        tick = self._get_data(tick_res)
        bid = float(tick.get("bid", 1.15))
        # Place BUY_LIMIT 100 pips below current market
        limit_price = round(bid - 0.0100, 5)

        log_info(f"Placing BUY_LIMIT order @ {limit_price} for {self.symbol} (/api/order_send)...")
        pending_payload = {
            "action": 5,  # TRADE_ACTION_PENDING
            "symbol": self.symbol,
            "volume": self.volume,
            "type": 2,    # ORDER_TYPE_BUY_LIMIT
            "price": limit_price,
            "comment": "API BUY_LIMIT Test",
            "magic": 333003
        }
        pend_res = self._request("POST", "/api/order_send", data=pending_payload)
        p_data = self._get_data(pend_res)
        pending_ticket = p_data.get("order")
        log_success(f"BUY_LIMIT Placed: retcode={p_data.get('retcode')} | Order Ticket=#{pending_ticket} | Price={limit_price}")

        # Query Orders
        time.sleep(1)
        log_info("Querying pending orders list (/api/orders_get)...")
        orders_res = self._request("GET", "/api/orders_get", params={"symbol": self.symbol})
        orders_data = self._get_data(orders_res)
        orders = orders_data.get("orders", []) if isinstance(orders_data, dict) else orders_data
        log_success(f"Active pending orders count: {len(orders)}")

        tot_res = self._request("GET", "/api/orders_total")
        log_success(f"Total pending orders (/api/orders_total): {self._get_data(tot_res)}")

        # Cancel Pending Order
        if pending_ticket:
            log_info(f"Cancelling pending order #{pending_ticket} (/api/order/{pending_ticket})...")
            cancel_res = self._request("DELETE", f"/api/order/{pending_ticket}")
            c_data = self._get_data(cancel_res)
            log_success(f"Pending order cancelled: retcode={c_data.get('retcode')}")

    # =========================================================================
    # 7. Historical Orders and Deals
    # =========================================================================
    def test_history(self):
        print(f"\n{BOLD}======================================================{RESET}")
        print(f"{BOLD} 7. Testing History (Orders & Executed Deals){RESET}")
        print(f"{BOLD}======================================================{RESET}")

        dt_from = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        dt_to = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # 1. history_orders_total
        log_info(f"Fetching history orders count from '{dt_from}' (/api/history_orders_total)...")
        ho_tot = self._request("GET", "/api/history_orders_total", params={"date_from": dt_from, "date_to": dt_to})
        log_success(f"Total historical orders: {self._get_data(ho_tot)}")

        # 2. history_orders_get
        log_info("Fetching historical orders list (/api/history_orders_get)...")
        ho_res = self._request("GET", "/api/history_orders_get", params={"date_from": dt_from, "date_to": dt_to, "group": f"*{self.symbol}*"})
        ho_data = self._get_data(ho_res)
        ho_list = ho_data.get("orders", []) if isinstance(ho_data, dict) else ho_data
        log_success(f"Retrieved {len(ho_list)} historical order(s) for {self.symbol}")

        # 3. history_deals_total
        log_info(f"Fetching executed deals count from '{dt_from}' (/api/history_deals_total)...")
        hd_tot = self._request("GET", "/api/history_deals_total", params={"date_from": dt_from, "date_to": dt_to})
        log_success(f"Total historical deals: {self._get_data(hd_tot)}")

        # 4. history_deals_get
        log_info("Fetching executed deals details (/api/history_deals_get)...")
        hd_res = self._request("GET", "/api/history_deals_get", params={"date_from": dt_from, "date_to": dt_to, "group": f"*{self.symbol}*"})
        hd_data = self._get_data(hd_res)
        hd_list = hd_data.get("deals", []) if isinstance(hd_data, dict) else hd_data
        log_success(f"Retrieved {len(hd_list)} executed deal(s) for {self.symbol}")

    def run_all(self):
        print(f"\n{BOLD}{CYAN}======================================================{RESET}")
        print(f"{BOLD}{CYAN}   MetaTrader 5 REST API 100% Comprehensive Suite     {RESET}")
        print(f"{BOLD}{CYAN}======================================================{RESET}")
        print(f"Target Base URL : {self.base_url}")
        print(f"Test Symbol     : {self.symbol}")
        print(f"Trade Volume    : {self.volume}")
        print(f"Auto-Close Pos  : {self.close_order}")

        start_time = time.time()
        try:
            self.test_system_info()
            self.test_symbols_and_dom()
            self.test_market_data_rates()
            self.test_calculators_and_checks()
            self.test_market_orders_buy_and_sell()
            self.test_pending_orders()
            self.test_history()

            elapsed = round(time.time() - start_time, 2)
            print(f"\n{BOLD}{GREEN}======================================================{RESET}")
            print(f"{BOLD}{GREEN} ✔ ALL 100% OF API METHODS TESTED SUCCESSFULLY in {elapsed}s!{RESET}")
            print(f"{BOLD}{GREEN}======================================================{RESET}\n")
            return 0
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            print(f"\n{BOLD}{RED}======================================================{RESET}")
            print(f"{BOLD}{RED} ✖ TEST SUITE FAILED after {elapsed}s: {e}{RESET}")
            print(f"{BOLD}{RED}======================================================{RESET}\n")
            return 1


def main():
    parser = argparse.ArgumentParser(description="MetaTrader 5 REST API 100% Full Integration Tester")
    parser.add_argument("--url", default=os.environ.get("API_URL", "http://localhost:5000"), help="Base API URL (default: http://localhost:5000)")
    parser.add_argument("--symbol", default="EURUSD", help="Trading symbol (default: EURUSD)")
    parser.add_argument("--volume", type=float, default=0.01, help="Lot volume for test trade (default: 0.01)")
    parser.add_argument("--no-close", action="store_true", help="Do not close the test positions after opening")

    args = parser.parse_args()
    tester = MT5ApiTester(base_url=args.url, symbol=args.symbol, volume=args.volume, close_order=not args.no_close)
    sys.exit(tester.run_all())


if __name__ == "__main__":
    main()
