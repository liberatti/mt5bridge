import os
import json
import socket
import logging

logger = logging.getLogger("mt5_gateway")


class StructObject(dict):
    """
    Dict subclass that allows attribute-style access and _asdict() compatibility
    with MetaTrader5 NamedTuple return types.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__dict__ = self

    def _asdict(self):
        return dict(self)


class Mt5GatewayClient:
    """
    Pure TCP Socket JSON client communicating directly with the MQL5 RestGateway
    Expert Advisor inside MetaTrader 5 (Port 22347).
    """

    # Timeframes
    TIMEFRAME_M1 = 1
    TIMEFRAME_M2 = 2
    TIMEFRAME_M3 = 3
    TIMEFRAME_M4 = 4
    TIMEFRAME_M5 = 5
    TIMEFRAME_M6 = 6
    TIMEFRAME_M10 = 10
    TIMEFRAME_M12 = 12
    TIMEFRAME_M15 = 15
    TIMEFRAME_M20 = 20
    TIMEFRAME_M30 = 30
    TIMEFRAME_H1 = 16385
    TIMEFRAME_H2 = 16386
    TIMEFRAME_H3 = 16387
    TIMEFRAME_H4 = 16388
    TIMEFRAME_H6 = 16390
    TIMEFRAME_H8 = 16392
    TIMEFRAME_H12 = 16396
    TIMEFRAME_D1 = 16408
    TIMEFRAME_W1 = 32769
    TIMEFRAME_MN1 = 49153

    # Copy Ticks
    COPY_TICKS_ALL = -1
    COPY_TICKS_INFO = 1
    COPY_TICKS_TRADE = 2

    # Order Types
    ORDER_TYPE_BUY = 0
    ORDER_TYPE_SELL = 1
    ORDER_TYPE_BUY_LIMIT = 2
    ORDER_TYPE_SELL_LIMIT = 3
    ORDER_TYPE_BUY_STOP = 4
    ORDER_TYPE_SELL_STOP = 5
    ORDER_TYPE_BUY_STOP_LIMIT = 6
    ORDER_TYPE_SELL_STOP_LIMIT = 7
    ORDER_TYPE_CLOSE_BY = 8

    # Order Time
    ORDER_TIME_GTC = 0
    ORDER_TIME_DAY = 1
    ORDER_TIME_SPECIFIED = 2
    ORDER_TIME_SPECIFIED_DAY = 3

    # Order Filling
    ORDER_FILLING_FOK = 0
    ORDER_FILLING_IOC = 1
    ORDER_FILLING_RETURN = 2
    ORDER_FILLING_BOC = 3

    # Trade Actions
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 5
    TRADE_ACTION_SLTP = 6
    TRADE_ACTION_MODIFY = 7
    TRADE_ACTION_REMOVE = 8
    TRADE_ACTION_CLOSE_BY = 10

    # Trade Retcodes
    TRADE_RETCODE_REQUOTE = 10004
    TRADE_RETCODE_REJECT = 10006
    TRADE_RETCODE_CANCEL = 10007
    TRADE_RETCODE_PLACED = 10008
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_DONE_PARTIAL = 10010
    TRADE_RETCODE_ERROR = 10011
    TRADE_RETCODE_TIMEOUT = 10012
    TRADE_RETCODE_INVALID = 10013
    TRADE_RETCODE_INVALID_VOLUME = 10014
    TRADE_RETCODE_INVALID_PRICE = 10015
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_TRADE_DISABLED = 10017
    TRADE_RETCODE_MARKET_CLOSED = 10018
    TRADE_RETCODE_NO_MONEY = 10019
    TRADE_RETCODE_PRICE_CHANGED = 10020
    TRADE_RETCODE_PRICE_OFF = 10021
    TRADE_RETCODE_INVALID_EXPIRATION = 10022
    TRADE_RETCODE_ORDER_CHANGED = 10023
    TRADE_RETCODE_TOO_MANY_REQUESTS = 10024
    TRADE_RETCODE_NO_CHANGES = 10025
    TRADE_RETCODE_SERVER_DISABLES_AT = 10026
    TRADE_RETCODE_CLIENT_DISABLES_AT = 10027
    TRADE_RETCODE_LOCKED = 10028
    TRADE_RETCODE_FROZEN = 10029
    TRADE_RETCODE_INVALID_FILL = 10030
    TRADE_RETCODE_CONNECTION = 10031
    TRADE_RETCODE_ONLY_REAL = 10032
    TRADE_RETCODE_LIMIT_ORDERS = 10033
    TRADE_RETCODE_LIMIT_VOLUME = 10034
    TRADE_RETCODE_POSITION_CLOSED = 10044

    def __init__(self, host="127.0.0.1", port=22347, timeout=10.0):
        self.host = host
        self.port = int(port)
        self.timeout = float(timeout)
        self._last_error = (0, "Success")

    def _send_request(
        self,
        action: str,
        params: dict = None,
        timeout: float = None,
        silent: bool = False,
    ) -> dict:
        req_payload = {}
        if params:
            req_payload.update(params)
            if "action" in params:
                req_payload["trade_action"] = params["action"]
                req_payload["order_type"] = params["action"]
        req_payload["action"] = action

        payload_bytes = (json.dumps(req_payload) + "\n").encode("utf-8")
        req_timeout = timeout or self.timeout

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(req_timeout)
                s.connect((self.host, self.port))
                s.sendall(payload_bytes)

                # Read response until EOF or trailing newline
                response_chunks = []
                while True:
                    try:
                        chunk = s.recv(65536)
                        if not chunk:
                            break
                        response_chunks.append(chunk)
                        if chunk.endswith(b"\n"):
                            break
                    except socket.timeout:
                        break

                raw_data = (
                    b"".join(response_chunks).decode("utf-8", errors="ignore").strip()
                )
                if not raw_data:
                    self._last_error = (
                        -1,
                        f"Empty response from MT5 gateway on action '{action}'",
                    )
                    raise RuntimeError(self._last_error[1])

                try:
                    res = json.loads(raw_data)
                except Exception as je:
                    self._last_error = (-1, f"Failed parsing JSON response on '{action}': {je}")
                    raise RuntimeError(self._last_error[1])

                if res.get("status") != "ok":
                    err_msg = res.get("error", "Unknown gateway error")
                    self._last_error = (res.get("code", -1), err_msg)
                    raise RuntimeError(f"MT5 Gateway Error on '{action}': {err_msg}")

                self._last_error = (0, "Success")
                return res.get("data", {})

        except Exception as e:
            self._last_error = (-1, str(e))
            if not silent:
                logger.warning("Gateway TCP request '%s' failed: %s", action, e)
            else:
                logger.debug("Gateway TCP request '%s' silent failure: %s", action, e)
            raise

    def last_error(self):
        return self._last_error

    def ping(self, timeout=1.0) -> bool:
        try:
            data = self._send_request("ping", timeout=timeout, silent=True)
            return bool(data.get("pong", False))
        except Exception:
            return False

    def initialize(self, **kwargs) -> bool:
        """
        Check if RestGateway TCP socket is alive and responding.
        """
        try:
            return self.ping()
        except Exception:
            return False

    def shutdown(self):
        return True

    def version(self):
        data = self._send_request("version")
        return (
            data.get("version", 500),
            data.get("build", 0),
            data.get("release_date", ""),
        )

    def terminal_info(self):
        data = self._send_request("terminal_info")
        return StructObject(data)

    def account_info(self):
        data = self._send_request("account_info")
        return StructObject(data)

    def symbols_total(self) -> int:
        data = self._send_request("symbols_total")
        return data.get("total", 0)

    def symbol_info(self, symbol: str):
        data = self._send_request("symbol_info", {"symbol": symbol})
        return StructObject(data)

    def symbol_info_tick(self, symbol: str):
        data = self._send_request("symbol_info_tick", {"symbol": symbol})
        return StructObject(data)

    def symbols_get(self, group: str = None):
        params = {}
        if group:
            params["group"] = group
        data = self._send_request("symbols_get", params)
        return [StructObject(item) for item in data]

    def copy_rates_from(self, symbol: str, timeframe: int, date_from, count: int):
        ts = (
            int(date_from.timestamp())
            if hasattr(date_from, "timestamp")
            else int(date_from)
        )
        data = self._send_request(
            "copy_rates_from",
            {
                "symbol": symbol,
                "timeframe": int(timeframe),
                "date_from": ts,
                "count": int(count),
            },
        )
        return [StructObject(r) for r in data]

    def copy_rates_from_pos(
        self, symbol: str, timeframe: int, start_pos: int, count: int
    ):
        data = self._send_request(
            "copy_rates_from_pos",
            {
                "symbol": symbol,
                "timeframe": int(timeframe),
                "start_pos": int(start_pos),
                "count": int(count),
            },
        )
        return [StructObject(r) for r in data]

    def copy_rates_range(self, symbol: str, timeframe: int, date_from, date_to):
        ts_from = (
            int(date_from.timestamp())
            if hasattr(date_from, "timestamp")
            else int(date_from)
        )
        ts_to = (
            int(date_to.timestamp()) if hasattr(date_to, "timestamp") else int(date_to)
        )
        data = self._send_request(
            "copy_rates_range",
            {
                "symbol": symbol,
                "timeframe": int(timeframe),
                "date_from": ts_from,
                "date_to": ts_to,
            },
        )
        return [StructObject(r) for r in data]

    def copy_ticks_from(self, symbol: str, date_from, count: int, flags: int = -1):
        ts = (
            int(date_from.timestamp())
            if hasattr(date_from, "timestamp")
            else int(date_from)
        )
        data = self._send_request(
            "copy_ticks_from",
            {
                "symbol": symbol,
                "date_from": ts,
                "count": int(count),
                "flags": int(flags),
            },
        )
        return [StructObject(t) for t in data]

    def copy_ticks_range(self, symbol: str, date_from, date_to, flags: int = -1):
        ts_from = (
            int(date_from.timestamp())
            if hasattr(date_from, "timestamp")
            else int(date_from)
        )
        ts_to = (
            int(date_to.timestamp()) if hasattr(date_to, "timestamp") else int(date_to)
        )
        data = self._send_request(
            "copy_ticks_range",
            {
                "symbol": symbol,
                "date_from": ts_from,
                "date_to": ts_to,
                "flags": int(flags),
            },
        )
        return [StructObject(t) for t in data]

    def positions_total(self) -> int:
        positions = self.positions_get()
        return len(positions) if positions else 0

    def positions_get(self, symbol: str = None, group: str = None, ticket: int = None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        if group:
            params["group"] = group
        if ticket:
            params["ticket"] = int(ticket)
        data = self._send_request("positions_get", params)
        return [StructObject(p) for p in data]

    def orders_total(self) -> int:
        orders = self.orders_get()
        return len(orders) if orders else 0

    def orders_get(self, symbol: str = None, group: str = None, ticket: int = None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        if group:
            params["group"] = group
        if ticket:
            params["ticket"] = int(ticket)
        data = self._send_request("orders_get", params)
        return [StructObject(o) for o in data]

    def order_send(self, request: dict):
        data = self._send_request("order_send", request)
        return StructObject(data)

    def order_check(self, request: dict):
        data = self._send_request("order_check", request)
        return StructObject(data)

    def order_calc_margin(self, action: int, symbol: str, volume: float, price: float):
        data = self._send_request(
            "order_calc_margin",
            {
                "action": int(action),
                "symbol": symbol,
                "volume": float(volume),
                "price": float(price),
            },
        )
        return data.get("margin", 0.0)

    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: float,
        price_open: float,
        price_close: float,
    ):
        data = self._send_request(
            "order_calc_profit",
            {
                "action": int(action),
                "symbol": symbol,
                "volume": float(volume),
                "price_open": float(price_open),
                "price_close": float(price_close),
            },
        )
        return data.get("profit", 0.0)

    def history_orders_get(
        self, date_from=None, date_to=None, group: str = None, ticket: int = None
    ):
        params = {}
        if date_from:
            params["date_from"] = (
                int(date_from.timestamp())
                if hasattr(date_from, "timestamp")
                else int(date_from)
            )
        if date_to:
            params["date_to"] = (
                int(date_to.timestamp())
                if hasattr(date_to, "timestamp")
                else int(date_to)
            )
        if group:
            params["group"] = group
        if ticket:
            params["ticket"] = int(ticket)
        data = self._send_request("history_orders_get", params)
        return [StructObject(o) for o in data]

    def history_deals_get(
        self,
        date_from=None,
        date_to=None,
        group: str = None,
        ticket: int = None,
        position: int = None,
    ):
        params = {}
        if date_from:
            params["date_from"] = (
                int(date_from.timestamp())
                if hasattr(date_from, "timestamp")
                else int(date_from)
            )
        if date_to:
            params["date_to"] = (
                int(date_to.timestamp())
                if hasattr(date_to, "timestamp")
                else int(date_to)
            )
        if group:
            params["group"] = group
        if ticket:
            params["ticket"] = int(ticket)
        if position:
            params["position"] = int(position)
        data = self._send_request("history_deals_get", params)
        return [StructObject(d) for d in data]

    def history_orders_total(self, date_from=None, date_to=None):
        orders = self.history_orders_get(date_from=date_from, date_to=date_to)
        return len(orders) if orders else 0

    def history_deals_total(self, date_from=None, date_to=None):
        deals = self.history_deals_get(date_from=date_from, date_to=date_to)
        return len(deals) if deals else 0

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        try:
            self._send_request("symbol_info", {"symbol": symbol})
            return True
        except Exception:
            return True

    def market_book_add(self, symbol: str) -> bool:
        return True

    def market_book_get(self, symbol: str):
        tick = self.symbol_info_tick(symbol)
        if not tick:
            return None
        return [
            StructObject(
                {
                    "type": 1,
                    "price": tick.get("ask", 0.0),
                    "volume": 10.0,
                    "volume_dbl": 10.0,
                }
            ),
            StructObject(
                {
                    "type": 2,
                    "price": tick.get("bid", 0.0),
                    "volume": 10.0,
                    "volume_dbl": 10.0,
                }
            ),
        ]

    def market_book_release(self, symbol: str) -> bool:
        return True

    def login(
        self, login: int, password: str = None, server: str = None, timeout: int = None
    ) -> bool:
        # Check if gateway is alive
        return self.ping()


# Global singleton instance
gateway_client = Mt5GatewayClient(
    host=os.environ.get("MT5_GATEWAY_HOST", "127.0.0.1"),
    port=int(os.environ.get("MT5_GATEWAY_PORT", "22347")),
    timeout=float(os.environ.get("MT5_GATEWAY_TIMEOUT", "10.0")),
)

# Export standard constants for compatibility
TIMEFRAME_M1 = 1
TIMEFRAME_M2 = 2
TIMEFRAME_M3 = 3
TIMEFRAME_M4 = 4
TIMEFRAME_M5 = 5
TIMEFRAME_M6 = 6
TIMEFRAME_M10 = 10
TIMEFRAME_M12 = 12
TIMEFRAME_M15 = 15
TIMEFRAME_M20 = 20
TIMEFRAME_M30 = 30
TIMEFRAME_H1 = 16385
TIMEFRAME_H2 = 16386
TIMEFRAME_H3 = 16387
TIMEFRAME_H4 = 16388
TIMEFRAME_H6 = 16390
TIMEFRAME_H8 = 16392
TIMEFRAME_H12 = 16396
TIMEFRAME_D1 = 16408
TIMEFRAME_W1 = 32769
TIMEFRAME_MN1 = 49153

COPY_TICKS_ALL = -1
COPY_TICKS_INFO = 1
COPY_TICKS_TRADE = 2

ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5
ORDER_TYPE_BUY_STOP_LIMIT = 6
ORDER_TYPE_SELL_STOP_LIMIT = 7
ORDER_TYPE_CLOSE_BY = 8

TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8
TRADE_ACTION_CLOSE_BY = 10
