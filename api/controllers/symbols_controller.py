from flask import Blueprint, request
from nxcore.controllers.base_controller import (
    has_any_authority,
    response_data,
    response_error,
)
from services.symbols_service import SymbolsService

symbols_bp = Blueprint("symbols", __name__)
service = SymbolsService()


@symbols_bp.route("/symbols_total", methods=["GET"])
@has_any_authority(_internal=True)
def api_symbols_total():
    """
    Get the total number of financial instruments available on the MetaTrader 5 server.

    Returns:
        Response: Standardized JSON with {"total": int}.
    """
    return response_data(service.symbols_total())


@symbols_bp.route("/symbols_get", methods=["GET"])
@has_any_authority(_internal=True)
def api_symbols_get():
    """
    Retrieve list of available instruments with optional wildcard filtering.

    Query Parameters:
        group (str, optional): Symbol mask filter pattern (e.g. '*USD*', '*EUR*'). Default: '*'.

    Returns:
        Response: Standardized JSON with {"count": int, "symbols": list[dict]}.
    """
    group = request.args.get("group", "*")
    symbols = service.symbols_get(group=group)
    return response_data({"count": len(symbols), "symbols": symbols})


@symbols_bp.route("/symbol_info/<symbol>", methods=["GET"])
@has_any_authority(_internal=True)
def api_symbol_info(symbol):
    """
    Get complete instrument specifications and market properties for a specific symbol.

    Path Parameters:
        symbol (str): Symbol name (e.g. 'EURUSD').

    Returns:
        Response: Standardized JSON with instrument specification dictionary.
    """
    return response_data(service.symbol_info(symbol))


@symbols_bp.route("/symbol_info_tick/<symbol>", methods=["GET"])
@has_any_authority(_internal=True)
def api_symbol_info_tick(symbol):
    """
    Get the latest market price tick (bid, ask, last, volume, timestamp) for a symbol.

    Path Parameters:
        symbol (str): Symbol name (e.g. 'EURUSD').

    Returns:
        Response: Standardized JSON with tick data dictionary and ISO timestamp.
    """
    try:
        return response_data(service.symbol_info_tick(symbol))
    except ValueError as e:
        return response_error(msg=str(e), code=404)


@symbols_bp.route("/symbol_select", methods=["POST"])
@has_any_authority(_internal=True)
def api_symbol_select():
    """
    Add or remove a symbol to/from the Market Watch window.

    JSON Body:
        symbol (str, required): Symbol name to select/unselect.
        enable (bool, optional): True to add, False to remove. Default: True.

    Returns:
        Response: Standardized JSON with {"symbol": str, "selected": bool}.
    """
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    enable = data.get("enable", True)
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    res = service.symbol_select(symbol, enable=enable)
    return response_data(res)


@symbols_bp.route("/market_book_add", methods=["POST"])
@has_any_authority(_internal=True)
def api_market_book_add():
    """
    Subscribe to Depth of Market (DOM / Order Book) data for a symbol.

    JSON Body:
        symbol (str, required): Symbol name to subscribe to.

    Returns:
        Response: Standardized JSON with {"symbol": str, "subscribed": bool}.
    """
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    return response_data(service.market_book_add(symbol))


@symbols_bp.route("/market_book_get/<symbol>", methods=["GET"])
@has_any_authority(_internal=True)
def api_market_book_get(symbol):
    """
    Get current Depth of Market (DOM / Order Book) entries for a symbol.

    Path Parameters:
        symbol (str): Symbol name.

    Returns:
        Response: Standardized JSON with list of DOM book entries (type, price, volume, volume_dbl).
    """
    return response_data(service.market_book_get(symbol))


@symbols_bp.route("/market_book_release", methods=["POST"])
@has_any_authority(_internal=True)
def api_market_book_release():
    """
    Unsubscribe from Depth of Market (DOM / Order Book) data for a symbol.

    JSON Body:
        symbol (str, required): Symbol name to unsubscribe from.

    Returns:
        Response: Standardized JSON with {"symbol": str, "released": bool}.
    """
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    if not symbol:
        return response_error(msg="Field 'symbol' is required", code=400)
    return response_data(service.market_book_release(symbol))
