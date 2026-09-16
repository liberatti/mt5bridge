from flask import Blueprint, request
from nxcore.controllers.base_controller import response_data, response_error
from services.symbols_service import SymbolsService

symbols_bp = Blueprint("symbols", __name__)
service = SymbolsService()


@symbols_bp.route("/symbols_total", methods=["GET"])
def api_symbols_total():
    return response_data(service.symbols_total())


@symbols_bp.route("/symbols_get", methods=["GET"])
def api_symbols_get():
    group = request.args.get("group", "*")
    symbols = service.symbols_get(group=group)
    return response_data({"count": len(symbols), "symbols": symbols})


@symbols_bp.route("/symbol_info/<symbol>", methods=["GET"])
def api_symbol_info(symbol):
    return response_data(service.symbol_info(symbol))


@symbols_bp.route("/symbol_info_tick/<symbol>", methods=["GET"])
def api_symbol_info_tick(symbol):
    return response_data(service.symbol_info_tick(symbol))


@symbols_bp.route("/symbol_select", methods=["POST"])
def api_symbol_select():
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    enable = data.get("enable", True)
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    res = service.symbol_select(symbol, enable=enable)
    return response_data(res)


@symbols_bp.route("/market_book_add", methods=["POST"])
def api_market_book_add():
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    return response_data(service.market_book_add(symbol))


@symbols_bp.route("/market_book_get/<symbol>", methods=["GET"])
def api_market_book_get(symbol):
    return response_data(service.market_book_get(symbol))


@symbols_bp.route("/market_book_release", methods=["POST"])
def api_market_book_release():
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    return response_data(service.market_book_release(symbol))
