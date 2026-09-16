from flask import Blueprint, request
from nxcore.controllers.base_controller import (
    response_data,
    response_error,
)
from services.trade_service import TradeService

trade_bp = Blueprint("trade", __name__)
service = TradeService()


@trade_bp.route("/order_check", methods=["POST"])
def api_order_check():
    """
    Simulate and check trading order validity and margin adequacy before dispatching to the broker.

    JSON Body:
        MqlTradeRequest JSON dictionary (action, symbol, volume, type, price, etc.).

    Returns:
        Response: Standardized JSON with MqlTradeCheckResult (retcode, balance, equity, margin, etc.).
    """
    data = request.get_json(force=True)
    res = service.order_check(data)
    return response_data(res)


@trade_bp.route("/order_send", methods=["POST"])
def api_order_send():
    """
    Send raw trade transaction request directly to the broker server.

    JSON Body:
        MqlTradeRequest JSON dictionary (action, symbol, volume, type, price, sl, tp, etc.).

    Returns:
        Response: Standardized JSON with MqlTradeResult (retcode, deal, order, volume, price, etc.).
    """
    data = request.get_json(force=True)
    res = service.order_send(data)
    return response_data(res)


@trade_bp.route("/order_calc_margin", methods=["POST"])
def api_order_calc_margin():
    """
    Calculate the required margin in the account currency for a proposed order.

    JSON Body:
        action (str or int, required): Order action / type ('BUY', 'SELL', etc.).
        symbol (str, required): Instrument symbol.
        volume (float, required): Lot size / volume.
        price (float, required): Proposed open price.

    Returns:
        Response: Standardized JSON with {"action": ..., "symbol": ..., "volume": float, "price": float, "margin": float}.
    """
    data = request.get_json(force=True)
    action = data.get("action")
    symbol = data.get("symbol")
    volume = data.get("volume")
    price = data.get("price")
    if action is None or not symbol or volume is None or price is None:
        return response_error(
            msg="Fields 'action', 'symbol', 'volume' and 'price' are required",
            code=400,
        )
    res = service.order_calc_margin(action, symbol, volume, price)
    return response_data(res)


@trade_bp.route("/order_calc_profit", methods=["POST"])
def api_order_calc_profit():
    """
    Calculate the projected profit/loss in the account currency for an order.

    JSON Body:
        action (str or int, required): Order action / type ('BUY', 'SELL', etc.).
        symbol (str, required): Instrument symbol.
        volume (float, required): Lot size / volume.
        price_open (float, required): Open price.
        price_close (float, required): Close price.

    Returns:
        Response: Standardized JSON with profit calculation details and projected profit value.
    """
    data = request.get_json(force=True)
    action = data.get("action")
    symbol = data.get("symbol")
    volume = data.get("volume")
    price_open = data.get("price_open")
    price_close = data.get("price_close")
    if (
        action is None
        or not symbol
        or volume is None
        or price_open is None
        or price_close is None
    ):
        return response_error(
            msg="Fields 'action', 'symbol', 'volume', 'price_open' and 'price_close' are required",
            code=400,
        )
    res = service.order_calc_profit(action, symbol, volume, price_open, price_close)
    return response_data(res)


@trade_bp.route("/orders_total", methods=["GET"])
def api_orders_total():
    """
    Get the total number of currently active pending orders.

    Returns:
        Response: Standardized JSON with {"total": int}.
    """
    return response_data(service.orders_total())


@trade_bp.route("/orders_get", methods=["GET"])
def api_orders_get():
    """
    Retrieve active pending orders with optional filtering.

    Query Parameters:
        symbol (str, optional): Filter by symbol name.
        group (str, optional): Symbol mask filter pattern (e.g. '*EUR*').
        ticket (int, optional): Unique pending order ticket.

    Returns:
        Response: Standardized JSON with {"count": int, "orders": list[dict]}.
    """
    symbol = request.args.get("symbol")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    orders = service.orders_get(symbol=symbol, group=group, ticket=ticket)
    return response_data({"count": len(orders), "orders": orders})


@trade_bp.route("/positions_total", methods=["GET"])
def api_positions_total():
    """
    Get the total count of currently open market positions.

    Returns:
        Response: Standardized JSON with {"total": int}.
    """
    return response_data(service.positions_total())


@trade_bp.route("/positions_get", methods=["GET"])
def api_positions_get():
    """
    Retrieve open market positions with optional filtering.

    Query Parameters:
        symbol (str, optional): Filter by symbol name.
        group (str, optional): Symbol mask filter pattern.
        ticket (int, optional): Unique position ticket.

    Returns:
        Response: Standardized JSON with {"count": int, "positions": list[dict]}.
    """
    symbol = request.args.get("symbol")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    pos = service.positions_get(symbol=symbol, group=group, ticket=ticket)
    return response_data({"count": len(pos), "positions": pos})


@trade_bp.route("/order/open", methods=["POST"])
def api_order_open():
    """
    High-level helper to open a market or pending order.

    JSON Body:
        symbol (str, required): Instrument symbol.
        type (str, optional): 'BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', etc. Default: 'BUY'.
        volume (float, required): Order volume / lot size.
        price (float, optional): Order price (auto-fetched for market orders).
        sl (float, optional): Stop Loss price.
        tp (float, optional): Take Profit price.
        deviation (int, optional): Max allowed slippage in points. Default: 20.
        comment (str, optional): Order comment string. Default: 'API Order'.
        magic (int, optional): Magic number identifier. Default: 0.
        type_filling (int, optional): Order filling mode override (FOK/IOC/RETURN).

    Returns:
        Response: Standardized JSON with trade result dictionary.
    """
    data = request.get_json(force=True)
    symbol = data.get("symbol")
    order_type = data.get("type", "BUY")
    volume = data.get("volume")

    if not symbol or volume is None:
        return response_error(
            msg="Fields 'symbol' and 'volume' are required", code=400
        )

    res = service.open_order(
        symbol=symbol,
        order_type_str=order_type,
        volume=volume,
        price=data.get("price"),
        sl=data.get("sl"),
        tp=data.get("tp"),
        deviation=data.get("deviation", 20),
        comment=data.get("comment", "API Order"),
        magic=data.get("magic", 0),
        type_filling=data.get("type_filling"),
    )
    return response_data(res)


@trade_bp.route("/order/close", methods=["POST"])
def api_order_close():
    """
    High-level helper to close an active open position by ticket.

    JSON Body:
        ticket (int, required): Position ticket ID to close.
        volume (float, optional): Volume to close (defaults to full position volume).
        deviation (int, optional): Max allowed slippage. Default: 20.
        comment (str, optional): Close order comment. Default: 'API Close'.

    Returns:
        Response: Standardized JSON with close trade result dictionary.
    """
    data = request.get_json(force=True)
    ticket = data.get("ticket")
    if not ticket:
        return response_error(msg="Field 'ticket' is required", code=400)

    res = service.close_position(
        ticket=ticket,
        volume=data.get("volume"),
        deviation=data.get("deviation", 20),
        comment=data.get("comment", "API Close"),
    )
    return response_data(res)


@trade_bp.route("/order/modify", methods=["POST"])
def api_order_modify():
    """
    High-level helper to modify Stop Loss (SL) and Take Profit (TP) of an open position.

    JSON Body:
        ticket (int, required): Position ticket ID.
        sl (float, optional): New Stop Loss price.
        tp (float, optional): New Take Profit price.

    Returns:
        Response: Standardized JSON with modify result dictionary.
    """
    data = request.get_json(force=True)
    ticket = data.get("ticket")
    if not ticket:
        return response_error(msg="Field 'ticket' is required", code=400)

    res = service.modify_position(
        ticket=ticket, sl=data.get("sl"), tp=data.get("tp")
    )
    return response_data(res)


@trade_bp.route("/order/<int:ticket>", methods=["DELETE"])
def api_order_cancel(ticket):
    """
    Cancel an active pending order by ticket ID.

    Path Parameters:
        ticket (int): Ticket number of the pending order to cancel.

    Returns:
        Response: Standardized JSON with cancel result dictionary.
    """
    res = service.cancel_order(ticket=ticket)
    return response_data(res)

