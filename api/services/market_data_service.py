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
    def copy_rates_from(self, symbol, timeframe, date_from, count):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        dt = parse_date(date_from)
        rates = mt5.copy_rates_from(symbol, tf, dt, int(count))
        if rates is None:
            raise RuntimeError(f"copy_rates_from failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        rates = mt5.copy_rates_from_pos(symbol, tf, int(start_pos), int(count))
        if rates is None:
            raise RuntimeError(f"copy_rates_from_pos failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_rates_range(self, symbol, timeframe, date_from, date_to):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        tf = parse_timeframe(timeframe)
        dt_from = parse_date(date_from)
        dt_to = parse_date(date_to)
        rates = mt5.copy_rates_range(symbol, tf, dt_from, dt_to)
        if rates is None:
            raise RuntimeError(f"copy_rates_range failed: {mt5.last_error()}")
        return format_rates(rates)

    def copy_ticks_from(self, symbol, date_from, count, flags="ALL"):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        dt = parse_date(date_from)
        flag_val = COPY_TICKS_MAP.get(str(flags).upper(), mt5.COPY_TICKS_ALL) if isinstance(flags, str) else int(flags)
        ticks = mt5.copy_ticks_from(symbol, dt, int(count), flag_val)
        if ticks is None:
            raise RuntimeError(f"copy_ticks_from failed: {mt5.last_error()}")
        return format_ticks(ticks)

    def copy_ticks_range(self, symbol, date_from, date_to, flags="ALL"):
        self.ensure_initialized()
        mt5.symbol_select(symbol, True)
        dt_from = parse_date(date_from)
        dt_to = parse_date(date_to)
        flag_val = COPY_TICKS_MAP.get(str(flags).upper(), mt5.COPY_TICKS_ALL) if isinstance(flags, str) else int(flags)
        ticks = mt5.copy_ticks_range(symbol, dt_from, dt_to, flag_val)
        if ticks is None:
            raise RuntimeError(f"copy_ticks_range failed: {mt5.last_error()}")
        return format_ticks(ticks)
