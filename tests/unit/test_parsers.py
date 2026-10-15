from datetime import datetime, timezone
import pytest

from utils.parsers import (
    parse_date,
    parse_timeframe,
    format_rates,
    format_ticks,
    TIMEFRAME_M1,
    TIMEFRAME_H1,
    TIMEFRAME_D1,
    ORDER_TYPE_BUY,
    ORDER_TYPE_SELL,
    ORDER_TYPE_BUY_LIMIT,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_PENDING,
    COPY_TICKS_ALL,
    TIMEFRAME_MAP,
    ORDER_TYPE_MAP,
    TRADE_ACTION_MAP,
    COPY_TICKS_MAP,
)


@pytest.mark.unit
class TestParseDate:
    def test_parse_none(self):
        assert parse_date(None) is None

    def test_parse_datetime_without_tz(self):
        dt = datetime(2025, 1, 15, 12, 0, 0)
        parsed = parse_date(dt)
        assert parsed.tzinfo == timezone.utc
        assert parsed.year == 2025

    def test_parse_datetime_with_tz(self):
        dt = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert parse_date(dt) == dt

    def test_parse_numeric_timestamp(self):
        ts = 1700000000
        parsed = parse_date(ts)
        assert parsed == datetime.fromtimestamp(ts, tz=timezone.utc)

    def test_parse_float_timestamp(self):
        ts = 1700000000.5
        parsed = parse_date(ts)
        assert parsed == datetime.fromtimestamp(ts, tz=timezone.utc)

    def test_parse_iso_string_with_z(self):
        parsed = parse_date("2025-01-15T10:30:00Z")
        assert parsed == datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)

    def test_parse_standard_datetime_string(self):
        parsed = parse_date("2025-01-15 10:30:00")
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 15
        assert parsed.hour == 10
        assert parsed.minute == 30

    def test_parse_date_only_string(self):
        parsed = parse_date("2025-01-15")
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 15

    def test_parse_brazilian_date_string(self):
        parsed = parse_date("15.01.2025")
        assert parsed.year == 2025
        assert parsed.month == 1
        assert parsed.day == 15

    def test_parse_invalid_string(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date("not-a-date")


@pytest.mark.unit
class TestParseTimeframe:
    def test_parse_valid_timeframes(self):
        assert parse_timeframe("M1") == TIMEFRAME_M1
        assert parse_timeframe("m1") == TIMEFRAME_M1
        assert parse_timeframe("H1") == TIMEFRAME_H1
        assert parse_timeframe("D1") == TIMEFRAME_D1

    def test_parse_int_passthrough(self):
        assert parse_timeframe(TIMEFRAME_H1) == TIMEFRAME_H1

    def test_parse_digit_string(self):
        assert parse_timeframe("16385") == TIMEFRAME_H1

    def test_parse_invalid_timeframe(self):
        with pytest.raises(ValueError, match="Invalid timeframe"):
            parse_timeframe("INVALID_TF")


@pytest.mark.unit
class TestFormatRates:
    def test_format_empty_and_none(self):
        assert format_rates(None) == []
        assert format_rates([]) == []

    def test_format_valid_dict_rates(self):
        raw = [
            {
                "time": 1700000000,
                "open": 1.1000,
                "high": 1.1050,
                "low": 1.0950,
                "close": 1.1020,
                "tick_volume": 150,
                "spread": 10,
                "real_volume": 500,
            }
        ]
        formatted = format_rates(raw)
        assert len(formatted) == 1
        item = formatted[0]
        assert item["time"] == 1700000000
        assert "time_iso" in item
        assert item["open"] == 1.1000
        assert item["high"] == 1.1050
        assert item["low"] == 1.0950
        assert item["close"] == 1.1020
        assert item["tick_volume"] == 150
        assert item["spread"] == 10
        assert item["real_volume"] == 500


@pytest.mark.unit
class TestFormatTicks:
    def test_format_empty_and_none(self):
        assert format_ticks(None) == []
        assert format_ticks([]) == []

    def test_format_valid_dict_ticks(self):
        raw = [
            {
                "time": 1700000000,
                "time_msc": 1700000000123,
                "bid": 1.1000,
                "ask": 1.1002,
                "last": 1.1001,
                "volume": 1.5,
                "flags": 6,
                "volume_real": 2.5,
            }
        ]
        formatted = format_ticks(raw)
        assert len(formatted) == 1
        item = formatted[0]
        assert item["time"] == 1700000000
        assert item["time_msc"] == 1700000000123
        assert "time_iso" in item
        assert item["bid"] == 1.1000
        assert item["ask"] == 1.1002
        assert item["volume"] == 1.5
        assert item["volume_real"] == 2.5


@pytest.mark.unit
class TestConstantsMaps:
    def test_timeframe_map(self):
        assert "M1" in TIMEFRAME_MAP
        assert "D1" in TIMEFRAME_MAP

    def test_order_type_map(self):
        assert ORDER_TYPE_MAP["BUY"] == ORDER_TYPE_BUY
        assert ORDER_TYPE_MAP["SELL"] == ORDER_TYPE_SELL
        assert ORDER_TYPE_MAP["BUY_LIMIT"] == ORDER_TYPE_BUY_LIMIT

    def test_trade_action_map(self):
        assert TRADE_ACTION_MAP["DEAL"] == TRADE_ACTION_DEAL
        assert TRADE_ACTION_MAP["PENDING"] == TRADE_ACTION_PENDING

    def test_copy_ticks_map(self):
        assert COPY_TICKS_MAP["ALL"] == COPY_TICKS_ALL
