from flask import Blueprint, request
from nxcore.controllers.base_controller import response_data, response_error
from services.market_data_service import MarketDataService

market_data_bp = Blueprint("market_data", __name__)
service = MarketDataService()


@market_data_bp.route("/copy_rates_from", methods=["GET"])
def api_copy_rates_from():
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
