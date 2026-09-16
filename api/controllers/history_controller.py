from flask import Blueprint, request
from nxcore.controllers.base_controller import response_data
from services.history_service import HistoryService

history_bp = Blueprint("history", __name__)
service = HistoryService()


@history_bp.route("/history_orders_total", methods=["GET"])
def api_history_orders_total():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    return response_data(service.history_orders_total(date_from, date_to))


@history_bp.route("/history_orders_get", methods=["GET"])
def api_history_orders_get():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    position = request.args.get("position")
    orders = service.history_orders_get(
        date_from=date_from,
        date_to=date_to,
        group=group,
        ticket=ticket,
        position=position,
    )
    return response_data({"count": len(orders), "orders": orders})


@history_bp.route("/history_deals_total", methods=["GET"])
def api_history_deals_total():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    return response_data(service.history_deals_total(date_from, date_to))


@history_bp.route("/history_deals_get", methods=["GET"])
def api_history_deals_get():
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    group = request.args.get("group")
    ticket = request.args.get("ticket")
    position = request.args.get("position")
    deals = service.history_deals_get(
        date_from=date_from,
        date_to=date_to,
        group=group,
        ticket=ticket,
        position=position,
    )
    return response_data({"count": len(deals), "deals": deals})

