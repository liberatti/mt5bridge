from datetime import datetime, timezone
from typing import Dict, List, Any
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService


class SymbolsService(BaseService):
    """
    Service for managing financial instruments, symbol specifications, live ticks, and DOM subscriptions.
    """

    def symbols_total(self) -> Dict[str, int]:
        """
        Get the total count of available symbols in the MetaTrader 5 terminal.

        Returns:
            dict: {"total": int}
        """
        self.ensure_initialized()
        return {"total": mt5.symbols_total()}

    def symbols_get(self, group: str = "*") -> List[Dict[str, Any]]:
        """
        Retrieve all available financial instruments, optionally filtered by a group pattern.

        Args:
            group (str, optional): Symbol mask filter pattern (e.g. '*USD*', '*EUR*'). Defaults to '*'.

        Returns:
            list[dict]: List of symbol info dictionaries.
        """
        self.ensure_initialized()
        symbols = mt5.symbols_get(group=group)
        if symbols is None:
            return []
        return [s._asdict() for s in symbols]

    def symbol_info(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve full specification properties for a given financial symbol.

        Args:
            symbol (str): Symbol name (e.g. 'EURUSD').

        Returns:
            dict: Symbol parameters (spread, point, digits, margin requirements, trade mode, etc.).

        Raises:
            ValueError: If the symbol is not found or cannot be selected.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        info = mt5.symbol_info(symbol)
        if info is None:
            raise ValueError(f"Symbol {symbol} not found: {mt5.last_error()}")
        return info._asdict()

    def symbol_info_tick(self, symbol: str) -> Dict[str, Any]:
        """
        Retrieve the latest market price tick for a symbol.

        Args:
            symbol (str): Symbol name (e.g. 'EURUSD').

        Returns:
            dict: Latest tick properties (bid, ask, last, volume, time, time_iso).

        Raises:
            ValueError: If tick data is not available for the symbol.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise ValueError(f"Tick for {symbol} not found: {mt5.last_error()}")
        res = tick._asdict()
        res["time_iso"] = datetime.fromtimestamp(res["time"], tz=timezone.utc).isoformat()
        return res

    def symbol_select(self, symbol: str, enable: bool = True) -> Dict[str, Any]:
        """
        Add or remove a symbol from the Market Watch window.

        Args:
            symbol (str): Symbol name.
            enable (bool, optional): True to show in Market Watch, False to hide. Defaults to True.

        Returns:
            dict: {"symbol": str, "selected": bool}

        Raises:
            ValueError: If the symbol could not be selected/deselected.
        """
        self.ensure_initialized()
        res = mt5.symbol_select(symbol, bool(enable))
        if not res:
            raise ValueError(f"Could not select symbol {symbol}: {mt5.last_error()}")
        return {"symbol": symbol, "selected": bool(enable)}

    def market_book_add(self, symbol: str) -> Dict[str, Any]:
        """
        Subscribe to Depth of Market (DOM / Order Book) events for a symbol.

        Args:
            symbol (str): Symbol name.

        Returns:
            dict: {"symbol": str, "subscribed": True}

        Raises:
            RuntimeError: If subscription failed.
        """
        self.ensure_initialized()
        res = mt5.market_book_add(symbol)
        if not res:
            raise RuntimeError(f"market_book_add failed for {symbol}: {mt5.last_error()}")
        return {"symbol": symbol, "subscribed": True}

    def market_book_get(self, symbol: str) -> List[Dict[str, Any]]:
        """
        Retrieve current Depth of Market (DOM / Order Book) records for a symbol.

        Args:
            symbol (str): Symbol name.

        Returns:
            list[dict]: Array of order book records (type, price, volume, volume_dbl).

        Raises:
            RuntimeError: If DOM data could not be retrieved.
        """
        self.ensure_initialized()
        items = mt5.market_book_get(symbol)
        if items is None:
            raise RuntimeError(f"market_book_get failed for {symbol}: {mt5.last_error()}")
        return [i._asdict() for i in items]

    def market_book_release(self, symbol: str) -> Dict[str, Any]:
        """
        Unsubscribe from Depth of Market (DOM / Order Book) events for a symbol.

        Args:
            symbol (str): Symbol name.

        Returns:
            dict: {"symbol": str, "released": bool}
        """
        self.ensure_initialized()
        res = mt5.market_book_release(symbol)
        return {"symbol": symbol, "released": bool(res)}
