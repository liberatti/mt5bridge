from datetime import datetime, timezone
from typing import Any, List, Dict, Union, Optional

# Standard MetaTrader 5 Timeframe Constants
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

# Order Type Constants
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
ORDER_TYPE_BUY_LIMIT = 2
ORDER_TYPE_SELL_LIMIT = 3
ORDER_TYPE_BUY_STOP = 4
ORDER_TYPE_SELL_STOP = 5
ORDER_TYPE_BUY_STOP_LIMIT = 6
ORDER_TYPE_SELL_STOP_LIMIT = 7
ORDER_TYPE_CLOSE_BY = 8

# Trade Action Constants
TRADE_ACTION_DEAL = 1
TRADE_ACTION_PENDING = 5
TRADE_ACTION_SLTP = 6
TRADE_ACTION_MODIFY = 7
TRADE_ACTION_REMOVE = 8
TRADE_ACTION_CLOSE_BY = 10

# Copy Ticks Flags
COPY_TICKS_ALL = -1
COPY_TICKS_INFO = 1
COPY_TICKS_TRADE = 2

TIMEFRAME_MAP = {
    "M1": TIMEFRAME_M1,
    "M2": TIMEFRAME_M2,
    "M3": TIMEFRAME_M3,
    "M4": TIMEFRAME_M4,
    "M5": TIMEFRAME_M5,
    "M6": TIMEFRAME_M6,
    "M10": TIMEFRAME_M10,
    "M12": TIMEFRAME_M12,
    "M15": TIMEFRAME_M15,
    "M20": TIMEFRAME_M20,
    "M30": TIMEFRAME_M30,
    "H1": TIMEFRAME_H1,
    "H2": TIMEFRAME_H2,
    "H3": TIMEFRAME_H3,
    "H4": TIMEFRAME_H4,
    "H6": TIMEFRAME_H6,
    "H8": TIMEFRAME_H8,
    "H12": TIMEFRAME_H12,
    "D1": TIMEFRAME_D1,
    "W1": TIMEFRAME_W1,
    "MN1": TIMEFRAME_MN1,
}

ORDER_TYPE_MAP = {
    "BUY": ORDER_TYPE_BUY,
    "SELL": ORDER_TYPE_SELL,
    "BUY_LIMIT": ORDER_TYPE_BUY_LIMIT,
    "SELL_LIMIT": ORDER_TYPE_SELL_LIMIT,
    "BUY_STOP": ORDER_TYPE_BUY_STOP,
    "SELL_STOP": ORDER_TYPE_SELL_STOP,
    "BUY_STOP_LIMIT": ORDER_TYPE_BUY_STOP_LIMIT,
    "SELL_STOP_LIMIT": ORDER_TYPE_SELL_STOP_LIMIT,
    "CLOSE_BY": ORDER_TYPE_CLOSE_BY,
}

TRADE_ACTION_MAP = {
    "DEAL": TRADE_ACTION_DEAL,
    "PENDING": TRADE_ACTION_PENDING,
    "SLTP": TRADE_ACTION_SLTP,
    "MODIFY": TRADE_ACTION_MODIFY,
    "REMOVE": TRADE_ACTION_REMOVE,
    "CLOSE_BY": TRADE_ACTION_CLOSE_BY,
}

COPY_TICKS_MAP = {
    "ALL": COPY_TICKS_ALL,
    "INFO": COPY_TICKS_INFO,
    "TRADE": COPY_TICKS_TRADE,
}


def parse_date(date_val: Optional[Any]) -> Optional[datetime]:
    """
    Parse timestamps, ISO 8601 strings, or standard date strings into timezone-aware datetime objects.

    Args:
        date_val (str, int, float, or datetime, optional): Input date representation.

    Returns:
        datetime, optional: Timezone-aware UTC datetime object, or None if input was None.

    Raises:
        ValueError: If the string format cannot be parsed.
    """
    if date_val is None:
        return None
    if isinstance(date_val, datetime):
        return date_val.replace(tzinfo=timezone.utc) if date_val.tzinfo is None else date_val
    if isinstance(date_val, (int, float)):
        return datetime.fromtimestamp(date_val, tz=timezone.utc)
    if isinstance(date_val, str):
        date_str = date_val.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%d.%m.%Y %H:%M:%S",
                "%d.%m.%Y",
            ):
                try:
                    return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
    raise ValueError(f"Invalid date format: {date_val}")


def parse_timeframe(tf_val: Union[str, int]) -> int:
    """
    Convert timeframe string (e.g. 'M1', 'H1', 'D1') or integer into MetaTrader 5 timeframe enum value.

    Args:
        tf_val (str or int): Timeframe name or raw integer constant.

    Returns:
        int: MetaTrader 5 timeframe integer.

    Raises:
        ValueError: If timeframe string is unknown.
    """
    if isinstance(tf_val, int):
        return tf_val
    if isinstance(tf_val, str):
        if tf_val.isdigit():
            return int(tf_val)
        tf = TIMEFRAME_MAP.get(tf_val.upper())
        if tf is not None:
            return tf
    raise ValueError(
        f"Invalid timeframe: {tf_val}. Valid strings: {list(TIMEFRAME_MAP.keys())}"
    )


def format_rates(rates: Optional[List[Any]]) -> List[Dict[str, Any]]:
    """
    Format OHLCV rate records into a serializable JSON dictionary list with UTC ISO timestamps.

    Args:
        rates (list): Array of raw rate tuples/dictionaries from MT5.

    Returns:
        list[dict]: Array of formatted candle dictionaries (time, time_iso, open, high, low, close, tick_volume, spread, real_volume).
    """
    if rates is None:
        return []
    res = []
    for r in rates:
        t_val = int(r["time"] if isinstance(r, dict) else getattr(r, "time"))
        res.append(
            {
                "time": t_val,
                "time_iso": datetime.fromtimestamp(t_val, tz=timezone.utc).isoformat(),
                "open": float(r["open"] if isinstance(r, dict) else getattr(r, "open")),
                "high": float(r["high"] if isinstance(r, dict) else getattr(r, "high")),
                "low": float(r["low"] if isinstance(r, dict) else getattr(r, "low")),
                "close": float(
                    r["close"] if isinstance(r, dict) else getattr(r, "close")
                ),
                "tick_volume": int(
                    r["tick_volume"]
                    if isinstance(r, dict)
                    else getattr(r, "tick_volume", 0)
                ),
                "spread": int(
                    r["spread"] if isinstance(r, dict) else getattr(r, "spread", 0)
                ),
                "real_volume": int(
                    r["real_volume"]
                    if isinstance(r, dict)
                    else getattr(r, "real_volume", 0)
                ),
            }
        )
    return res


def format_ticks(ticks: Optional[List[Any]]) -> List[Dict[str, Any]]:
    """
    Format price tick records into a serializable JSON dictionary list with UTC ISO timestamps.

    Args:
        ticks (list): Array of raw tick tuples/dictionaries from MT5.

    Returns:
        list[dict]: Array of formatted tick dictionaries (time, time_msc, time_iso, bid, ask, last, volume, flags, volume_real).
    """
    if ticks is None:
        return []
    res = []
    for t in ticks:
        t_val = int(t["time"] if isinstance(t, dict) else getattr(t, "time"))
        t_msc = int(
            t.get("time_msc", t_val * 1000)
            if isinstance(t, dict)
            else getattr(t, "time_msc", t_val * 1000)
        )
        vol_real = float(
            t.get("volume_real", 0.0)
            if isinstance(t, dict)
            else getattr(t, "volume_real", 0.0)
        )
        res.append(
            {
                "time": t_val,
                "time_msc": t_msc,
                "time_iso": datetime.fromtimestamp(t_val, tz=timezone.utc).isoformat(),
                "bid": float(t["bid"] if isinstance(t, dict) else getattr(t, "bid")),
                "ask": float(t["ask"] if isinstance(t, dict) else getattr(t, "ask")),
                "last": float(
                    t.get("last", 0.0)
                    if isinstance(t, dict)
                    else getattr(t, "last", 0.0)
                ),
                "volume": float(
                    t.get("volume", 0.0)
                    if isinstance(t, dict)
                    else getattr(t, "volume", 0.0)
                ),
                "flags": int(
                    t.get("flags", 0) if isinstance(t, dict) else getattr(t, "flags", 0)
                ),
                "volume_real": vol_real,
            }
        )
    return res
