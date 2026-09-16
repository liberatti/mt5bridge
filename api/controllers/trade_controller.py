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
    data = request.get_json(force=True)
    res = service.order_check(data)
    return response_data(res)


@trade_bp.route("/order_send", methods=["POST"])
def api_order_send():
    data = request.get_json(force=True)
    res = service.order_send(data)
    return response_data(res)


@trade_bp.route("/order_calc_margin", methods=["POST"])
def api_order_calc_margin():
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
    return response_data(service.orders_total())


@trade_bp.route("/orders_get", methods=["GET"])
def api_orders_get():
    symbol = request.args.get("symbol")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    orders = service.orders_get(symbol=symbol, group=group, ticket=ticket)
    return response_data({"count": len(orders), "orders": orders})


@trade_bp.route("/positions_total", methods=["GET"])
def api_positions_total():
    return response_data(service.positions_total())


@trade_bp.route("/positions_get", methods=["GET"])
def api_positions_get():
    symbol = request.args.get("symbol")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    pos = service.positions_get(symbol=symbol, group=group, ticket=ticket)
    return response_data({"count": len(pos), "positions": pos})


@trade_bp.route("/order/open", methods=["POST"])
def api_order_open():
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
    res = service.cancel_order(ticket=ticket)
    return response_data(res)
