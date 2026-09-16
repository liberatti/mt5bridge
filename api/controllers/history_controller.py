from flask import Blueprint, request
from nxcore.controllers.base_controller import has_any_authority, response_data
from services.history_service import HistoryService

history_bp = Blueprint("history", __name__)
service = HistoryService()


@history_bp.route("/history_orders_total", methods=["GET"])
@has_any_authority(_internal=True)
def api_history_orders_total():
    """
    Get the total number of orders in trading history within an optional date range.

    Query Parameters:
        date_from (str, optional): Start datetime (ISO string, unix timestamp, or YYYY-MM-DD).
        date_to (str, optional): End datetime (ISO string, unix timestamp, or YYYY-MM-DD).

    Returns:
        Response: Standardized JSON with {"total": int}.
    """
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    return response_data(service.history_orders_total(date_from, date_to))


@history_bp.route("/history_orders_get", methods=["GET"])
@has_any_authority(_internal=True)
def api_history_orders_get():
    """
    Retrieve historical closed or canceled orders matching filter criteria.

    Query Parameters:
        date_from (str, optional): Start datetime filter.
        date_to (str, optional): End datetime filter.
        group (str, optional): Symbol mask/filter pattern (e.g. '*EUR*').
        ticket (int, optional): Unique order ticket identifier.
        position (int, optional): Position identifier associated with the orders.

    Returns:
        Response: Standardized JSON with {"count": int, "orders": list[dict]}.
    """
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
@has_any_authority(_internal=True)
def api_history_deals_total():
    """
    Get the total number of executed deals (trades) in history within an optional date range.

    Query Parameters:
        date_from (str, optional): Start datetime filter.
        date_to (str, optional): End datetime filter.

    Returns:
        Response: Standardized JSON with {"total": int}.
    """
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")
    return response_data(service.history_deals_total(date_from, date_to))


@history_bp.route("/history_deals_get", methods=["GET"])
@has_any_authority(_internal=True)
def api_history_deals_get():
    """
    Retrieve historical executed trade deals matching filter criteria.

    Query Parameters:
        date_from (str, optional): Start datetime filter.
        date_to (str, optional): End datetime filter.
        group (str, optional): Symbol mask/filter pattern (e.g. '*EUR*').
        ticket (int, optional): Unique deal ticket identifier.
        position (int, optional): Position identifier associated with the deals.

    Returns:
        Response: Standardized JSON with {"count": int, "deals": list[dict]}.
    """
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

