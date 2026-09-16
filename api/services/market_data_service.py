from typing import List, Dict, Any, Union
from services.mt5_gateway import gateway_client as mt5
from services.base_service import BaseService
from utils.parsers import (
    parse_date,
    parse_timeframe,
    format_rates,
    format_ticks,
    COPY_TICKS_MAP,
)


class MarketDataService(BaseService):
    """
    Service for fetching historical candlestick/bar rates and raw tick streams.
    """

    def copy_rates_from(
        self,
        symbol: str,
        timeframe: Union[str, int],
        date_from: Any,
        count: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candle rates starting backwards from a specific date.

        Args:
            symbol (str): Financial instrument symbol (e.g. 'EURUSD').
            timeframe (str or int): Bar timeframe (e.g. 'M1', 'H1', 'D1').
            date_from (str, int, or datetime): Starting date/time.
            count (int): Maximum number of bars to retrieve.

        Returns:
            list[dict]: Array of formatted OHLCV bar records.

        Raises:
            RuntimeError: If data retrieval fails.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        dt = parse_date(date_from)
        rates = mt5.copy_rates_from(symbol, tf, dt, int(count))
        if rates is None:
            raise RuntimeError(f"copy_rates_from failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: Union[str, int],
        start_pos: int,
        count: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candle rates starting backwards from an index position offset.

        Args:
            symbol (str): Financial instrument symbol.
            timeframe (str or int): Bar timeframe.
            start_pos (int): Starting bar index (0 = latest/current bar).
            count (int): Maximum number of bars to retrieve.

        Returns:
            list[dict]: Array of formatted OHLCV bar records.

        Raises:
            RuntimeError: If data retrieval fails.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        rates = mt5.copy_rates_from_pos(symbol, tf, int(start_pos), int(count))
        if rates is None:
            raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_rates_range(
        self,
        symbol: str,
        timeframe: Union[str, int],
        date_from: Any,
        date_to: Any,
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical candle rates within a specific datetime range.

        Args:
            symbol (str): Financial instrument symbol.
            timeframe (str or int): Bar timeframe.
            date_from (str, int, or datetime): Range start date/time.
            date_to (str, int, or datetime): Range end date/time.

        Returns:
            list[dict]: Array of formatted OHLCV bar records.

        Raises:
            RuntimeError: If data retrieval fails.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        dt_from = parse_date(date_from)
        dt_to = parse_date(date_to)
        rates = mt5.copy_rates_range(symbol, tf, dt_from, dt_to)
        if rates is None:
            raise RuntimeError(f"copy_rates_range failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_ticks_from(
        self,
        symbol: str,
        date_from: Any,
        count: int,
        flags: Union[str, int] = "ALL",
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw price ticks starting backwards from a specific date.

        Args:
            symbol (str): Financial instrument symbol.
            date_from (str, int, or datetime): Starting date/time.
            count (int): Maximum number of ticks to retrieve.
            flags (str or int, optional): Tick flags filter ('ALL', 'INFO', 'TRADE'). Defaults to 'ALL'.

        Returns:
            list[dict]: Array of formatted price tick records.

        Raises:
            RuntimeError: If tick data retrieval fails.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        dt = parse_date(date_from)
        flag_val = COPY_TICKS_MAP.get(str(flags).upper(), mt5.COPY_TICKS_ALL) if isinstance(flags, str) else int(flags)
        ticks = mt5.copy_ticks_from(symbol, dt, int(count), flag_val)
        if ticks is None:
            raise RuntimeError(f"copy_ticks_from failed: {mt5.last_error()}")
        return format_ticks(ticks)

    def copy_ticks_range(
        self,
        symbol: str,
        date_from: Any,
        date_to: Any,
        flags: Union[str, int] = "ALL",
    ) -> List[Dict[str, Any]]:
        """
        Fetch raw price ticks within a specific datetime range.

        Args:
            symbol (str): Financial instrument symbol.
            date_from (str, int, or datetime): Range start date/time.
            date_to (str, int, or datetime): Range end date/time.
            flags (str or int, optional): Tick flags filter ('ALL', 'INFO', 'TRADE'). Defaults to 'ALL'.

        Returns:
            list[dict]: Array of formatted price tick records.

        Raises:
            RuntimeError: If tick data retrieval fails.
        """
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        dt_from = parse_date(date_from)
        dt_to = parse_date(date_to)
        flag_val = COPY_TICKS_MAP.get(str(flags).upper(), mt5.COPY_TICKS_ALL) if isinstance(flags, str) else int(flags)
        ticks = mt5.copy_ticks_range(symbol, dt_from, dt_to, flag_val)
        if ticks is None:
            raise RuntimeError(f"copy_ticks_range failed: {mt5.last_error()}")
        return format_ticks(ticks)

