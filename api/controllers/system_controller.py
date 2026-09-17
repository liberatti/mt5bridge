from flask import Blueprint, request
from nxcore.controllers.base_controller import has_any_authority, response_data, response_error
from services.system_service import SystemService

system_bp = Blueprint("system", __name__)
service = SystemService()


@system_bp.route("/version", methods=["GET"])
@has_any_authority(_internal=True)
def api_version():
    """
    Get MetaTrader 5 terminal version, build number, and release date.

    Returns:
        Response: Standardized JSON with {"version": int, "build": int, "release_date": str}.
    """
    return response_data(service.version())


@system_bp.route("/last_error", methods=["GET"])
@has_any_authority(_internal=True)
def api_last_error():
    """
    Get the last error code and error description from the MetaTrader 5 terminal.

    Returns:
        Response: Standardized JSON with {"code": int, "description": str}.
    """
    return response_data(service.last_error())


@system_bp.route("/terminal_info", methods=["GET"])
@has_any_authority(_internal=True)
def api_terminal_info():
    """
    Get current MetaTrader 5 terminal status, connection state, build and paths.

    Returns:
        Response: Standardized JSON with full terminal info dictionary.
    """
    return response_data(service.terminal_info())


@system_bp.route("/account_info", methods=["GET"])
@has_any_authority(_internal=True)
def api_account_info():
    """
    Get account balance, equity, margin, free margin, leverage, and profit.

    Returns:
        Response: Standardized JSON with full account info dictionary.
    """
    return response_data(service.account_info())


@system_bp.route("/login", methods=["POST"])
@has_any_authority(_internal=True)
def api_login():
    """
    Authenticate MetaTrader 5 dynamically with new account credentials.

    Request Body (JSON):
        login (int): MT5 account login ID.
        password (str): MT5 account password.
        server (str): MT5 broker server name (e.g. XPMT5-DEMO).
        symbol (str, optional): Default symbol for chart startup (e.g. PETR4).

    Returns:
        Response: Standardized JSON with updated account info.
    """
    data = request.get_json(silent=True) or {}
    login_id = data.get("login")
    password = data.get("password")
    server = data.get("server")
    symbol = data.get("symbol")

    if not login_id or not password or not server:
        return response_error("Missing required fields: login, password, and server are required.", code=400)

    try:
        login_int = int(login_id)
    except (ValueError, TypeError):
        return response_error("Field 'login' must be a valid integer.", code=400)

    try:
        result = service.login(
            login=login_int,
            password=str(password),
            server=str(server),
            symbol=str(symbol) if symbol else None,
        )
        return response_data(result)
    except Exception as exc:
        return response_error(f"Falha ao realizar login no terminal MT5: {exc}", code=500)
