from flask import Blueprint
from nxcore.controllers.base_controller import response_data
from services.system_service import SystemService

system_bp = Blueprint("system", __name__)
service = SystemService()


@system_bp.route("/version", methods=["GET"])
def api_version():
    """
    Get MetaTrader 5 terminal version, build number, and release date.

    Returns:
        Response: Standardized JSON with {"version": int, "build": int, "release_date": str}.
    """
    return response_data(service.version())


@system_bp.route("/last_error", methods=["GET"])
def api_last_error():
    """
    Get the last error code and error description from the MetaTrader 5 terminal.

    Returns:
        Response: Standardized JSON with {"code": int, "description": str}.
    """
    return response_data(service.last_error())


@system_bp.route("/terminal_info", methods=["GET"])
def api_terminal_info():
    """
    Get current MetaTrader 5 terminal status, connection state, build and paths.

    Returns:
        Response: Standardized JSON with full terminal info dictionary.
    """
    return response_data(service.terminal_info())


@system_bp.route("/account_info", methods=["GET"])
def api_account_info():
    """
    Get account balance, equity, margin, free margin, leverage, and profit.

    Returns:
        Response: Standardized JSON with full account info dictionary.
    """
    return response_data(service.account_info())

