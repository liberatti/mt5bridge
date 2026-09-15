"""
Centralized route and blueprint registration for MetaTrader 5 Flask REST API.
"""

import os
from flask import render_template, send_from_directory, request

from controllers.system_controller import system_bp
from controllers.symbols_controller import symbols_bp
from controllers.market_data_controller import market_data_bp
from controllers.trade_controller import trade_bp
from controllers.history_controller import history_bp


def register_routes(app):
    """
    Registers all controllers, modular blueprints, and documentation routes to the Flask application.
    """
    templates_dir = os.path.join(app.root_path, "templates")

    # 1. Root route - Swagger UI Documentation
    @app.route("/", methods=["GET"])
    def index():
        format_param = request.args.get("format", "").lower()
        if format_param == "json" or (
            request.accept_mimetypes.best == "application/json"
            and not request.accept_mimetypes.accept_html
        ):
            return send_from_directory(
                templates_dir, "swagger.json", mimetype="application/json"
            )
        return render_template("swagger.html")

    # 2. OpenAPI 3.0 specification endpoint
    @app.route("/swagger.json", methods=["GET"])
    def swagger_spec():
        return send_from_directory(
            templates_dir, "swagger.json", mimetype="application/json"
        )

    # 3. Favicon route (prevent 404 logs)
    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        return "", 204

    # 3. Register Blueprints with URL prefix /api
    app.register_blueprint(system_bp, url_prefix="/api")
    app.register_blueprint(symbols_bp, url_prefix="/api")
    app.register_blueprint(market_data_bp, url_prefix="/api")
    app.register_blueprint(trade_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")


# Alias for backward compatibility
register = register_routes
