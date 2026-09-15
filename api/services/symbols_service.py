from datetime import datetime, timezone
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService


class SymbolsService(BaseService):
    def symbols_total(self):
        self.ensure_initialized()
        return {"total": mt5.symbols_total()}

    def symbols_get(self, group="*"):
        self.ensure_initialized()
        symbols = mt5.symbols_get(group=group)
        if symbols is None:
            return []
        return [s._asdict() for s in symbols]

    def symbol_info(self, symbol):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Symbol {symbol} not found: {mt5.last_error()}")
        return info._asdict()

    def symbol_info_tick(self, symbol):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Tick for {symbol} not found: {mt5.last_error()}")
        res = tick._asdict()
        res["time_iso"] = datetime.fromtimestamp(res["time"], tz=timezone.utc).isoformat()
        return res

    def symbol_select(self, symbol, enable=True):
        self.ensure_initialized()
        res = mt5.symbol_select(symbol, bool(enable))
        if not res:
            raise ValueError(f"Could not select symbol {symbol}: {mt5.last_error()}")
        return {"symbol": symbol, "selected": bool(enable)}

    def market_book_add(self, symbol):
        self.ensure_initialized()
        res = mt5.market_book_add(symbol)
        if not res:
            raise RuntimeError(f"market_book_add failed for {symbol}: {mt5.last_error()}")
        return {"symbol": symbol, "subscribed": True}

    def market_book_get(self, symbol):
        self.ensure_initialized()
        items = mt5.market_book_get(symbol)
        if items is None:
            raise RuntimeError(f"market_book_get failed for {symbol}: {mt5.last_error()}")
        return [i._asdict() for i in items]

    def market_book_release(self, symbol):
        self.ensure_initialized()
        res = mt5.market_book_release(symbol)
        return {"symbol": symbol, "released": bool(res)}
