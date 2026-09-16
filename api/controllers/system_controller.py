from flask import Blueprint
from nxcore.controllers.base_controller import response_data
from services.system_service import SystemService

system_bp = Blueprint("system", __name__)
service = SystemService()


@system_bp.route("/version", methods=["GET"])
def api_version():
    return response_data(service.version())


@system_bp.route("/last_error", methods=["GET"])
def api_last_error():
    return response_data(service.last_error())


@system_bp.route("/terminal_info", methods=["GET"])
def api_terminal_info():
    return response_data(service.terminal_info())


@system_bp.route("/account_info", methods=["GET"])
def api_account_info():
    return response_data(service.account_info())

