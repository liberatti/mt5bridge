from flask import Blueprint, request
from nxcore.controllers.base_controller import response_data, response_error
from services.market_data_service import MarketDataService

market_data_bp = Blueprint("market_data", __name__)
service = MarketDataService()


@market_data_bp.route("/copy_rates_from", methods=["GET"])
def api_copy_rates_from():
    """
    Get historical candle rates starting backwards from a specified datetime.

    Query Parameters:
        symbol (str, required): Instrument symbol (e.g. 'EURUSD').
        timeframe (str, optional): Bar timeframe (e.g. 'M1', 'M5', 'H1', 'D1'). Default: 'M1'.
        date_from (str, required): Start date/time (ISO 8601, timestamp, or YYYY-MM-DD).
        count (int, optional): Number of candles to retrieve. Default: 100.

    Returns:
        Response: Standardized JSON with {"symbol": str, "timeframe": str, "count": int, "rates": list[dict]}.
    """
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe", "M1")
    date_from = request.args.get("date_from")
    count = int(request.args.get("count", 100))

    if not symbol or not date_from:
        return response_error(
            msg="Parameters 'symbol' and 'date_from' are required",
            code=400,
        )

    rates = service.copy_rates_from(symbol, timeframe, date_from, count)
    return response_data(
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(rates),
            "rates": rates,
        }
    )


@market_data_bp.route("/copy_rates_from_pos", methods=["GET"])
def api_copy_rates_from_pos():
    """
    Get historical candle rates starting backwards from an index position offset.

    Query Parameters:
        symbol (str, required): Instrument symbol (e.g. 'EURUSD').
        timeframe (str, optional): Bar timeframe (e.g. 'M1', 'M5', 'H1', 'D1'). Default: 'M1'.
        start_pos (int, optional): Starting bar index (0 = latest/current bar). Default: 0.
        count (int, optional): Number of candles to retrieve. Default: 100.

    Returns:
        Response: Standardized JSON with {"symbol": str, "timeframe": str, "count": int, "rates": list[dict]}.
    """
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe", "M1")
    start_pos = int(request.args.get("start_pos", request.args.get("pos", 0)))
    count = int(request.args.get("count", 100))

    if not symbol:
        return response_error(
            msg="Parameter 'symbol' is required", code=400
        )

    rates = service.copy_rates_from_pos(symbol, timeframe, start_pos, count)
    return response_data(
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(rates),
            "rates": rates,
        }
    )


@market_data_bp.route("/copy_rates_range", methods=["GET"])
def api_copy_rates_range():
    """
    Get historical candle rates within a specific datetime range.

    Query Parameters:
        symbol (str, required): Instrument symbol.
        timeframe (str, optional): Bar timeframe. Default: 'M1'.
        date_from (str, required): Range start datetime.
        date_to (str, required): Range end datetime.

    Returns:
        Response: Standardized JSON with {"symbol": str, "timeframe": str, "count": int, "rates": list[dict]}.
    """
    symbol = request.args.get("symbol")
    timeframe = request.args.get("timeframe", "M1")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    if not symbol or not date_from or not date_to:
        return response_error(
            msg="Parameters 'symbol', 'date_from' and 'date_to' are required",
            code=400,
        )

    rates = service.copy_rates_range(symbol, timeframe, date_from, date_to)
    return response_data(
        {
            "symbol": symbol,
            "timeframe": timeframe,
            "count": len(rates),
            "rates": rates,
        }
    )


@market_data_bp.route("/copy_ticks_from", methods=["GET"])
def api_copy_ticks_from():
    """
    Get raw price ticks starting backwards from a specified datetime.

    Query Parameters:
        symbol (str, required): Instrument symbol.
        date_from (str, required): Start datetime.
        count (int, optional): Number of ticks to retrieve. Default: 100.
        flags (str, optional): Tick flags filter ('ALL', 'INFO', 'TRADE'). Default: 'ALL'.

    Returns:
        Response: Standardized JSON with {"symbol": str, "count": int, "ticks": list[dict]}.
    """
    symbol = request.args.get("symbol")
    date_from = request.args.get("date_from")
    count = int(request.args.get("count", 100))
    flags = request.args.get("flags", "ALL")

    if not symbol or not date_from:
        return response_error(
            msg="Parameters 'symbol' and 'date_from' are required",
            code=400,
        )

    ticks = service.copy_ticks_from(symbol, date_from, count, flags)
    return response_data({"symbol": symbol, "count": len(ticks), "ticks": ticks})


@market_data_bp.route("/copy_ticks_range", methods=["GET"])
def api_copy_ticks_range():
    """
    Get raw price ticks within a specific datetime range.

    Query Parameters:
        symbol (str, required): Instrument symbol.
        date_from (str, required): Range start datetime.
        date_to (str, required): Range end datetime.
        flags (str, optional): Tick flags filter ('ALL', 'INFO', 'TRADE'). Default: 'ALL'.

    Returns:
        Response: Standardized JSON with {"symbol": str, "count": int, "ticks": list[dict]}.
    """
    symbol = request.args.get("symbol")
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    flags = request.args.get("flags", "ALL")

    if not symbol or not date_from or not date_to:
        return response_error(
            msg="Parameters 'symbol', 'date_from' and 'date_to' are required",
            code=400,
        )

    ticks = service.copy_ticks_range(symbol, date_from, date_to, flags)
    return response_data({"symbol": symbol, "count": len(ticks), "ticks": ticks})

