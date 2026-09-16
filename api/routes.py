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
        """
        Serve the interactive Swagger UI HTML dashboard or OpenAPI JSON specification.

        Query Parameters:
            format (str, optional): Pass 'json' to receive raw OpenAPI specification.

        Returns:
            Response: Rendered Swagger HTML page or OpenAPI JSON spec.
        """
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
        """
        Serve the OpenAPI 3.0 JSON specification file for schema validation and client generation.

        Returns:
            Response: application/json file response containing the complete OpenAPI spec.
        """
        return send_from_directory(
            templates_dir, "swagger.json", mimetype="application/json"
        )

    # 3. Favicon and branding asset routes
    @app.route("/favicon.ico", methods=["GET"])
    def favicon():
        """
        Favicon handler serving the project icon.
        """
        if os.path.exists(os.path.join(templates_dir, "icon.svg")):
            return send_from_directory(
                templates_dir, "icon.svg", mimetype="image/svg+xml"
            )
        return "", 204

    @app.route("/logo.svg", methods=["GET"])
    def logo_svg():
        """
        Serve the MT5Bridge SVG banner logo.
        """
        return send_from_directory(
            templates_dir, "logo.svg", mimetype="image/svg+xml"
        )

    @app.route("/icon.svg", methods=["GET"])
    def icon_svg():
        """
        Serve the MT5Bridge SVG icon.
        """
        return send_from_directory(
            templates_dir, "icon.svg", mimetype="image/svg+xml"
        )



    # 3. Register Blueprints with URL prefix /api
    app.register_blueprint(system_bp, url_prefix="/api")
    app.register_blueprint(symbols_bp, url_prefix="/api")
    app.register_blueprint(market_data_bp, url_prefix="/api")
    app.register_blueprint(trade_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")


# Alias for backward compatibility
register = register_routes
