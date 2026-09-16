import os
import time
import logging
import threading
from flask import Flask
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

from nxcore.middleware.logging_manager import LoggingManager
from nxcore.controllers.base_controller import response_error, response_error_500
from routes import register_routes

logger = logging.getLogger("flask_app")


def create_app() -> Flask:
    """
    Application factory creating and configuring the Flask REST API application.

    Initializes logging middleware, CORS, global exception handlers, blueprints,
    Swagger documentation routes, and launches background auto-initialization for MetaTrader 5.

    Returns:
        Flask: Fully configured Flask application instance.
    """
    app = Flask(__name__, template_folder="templates")
    LoggingManager(app)
    CORS(app)

    # 1. Global Error handling
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return response_error(msg=e.description, code=e.code)

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("API Error: %s", e)
        return response_error_500(msg=str(e), details=str(e))

    # 2. Register all documentation and modular API routes
    register_routes(app)

    # 4. Auto-initialize MetaTrader 5 connection on server startup in background
    def _bg_init():
        try:
            time.sleep(1)
            from services.base_service import BaseService
            BaseService.ensure_initialized()
        except Exception as e:
            logger.warning("MetaTrader 5 background auto-initialization deferred: %s", e)

    threading.Thread(target=_bg_init, daemon=True).start()

    return app



# WSGI application instance (for Gunicorn / Waitress / uWSGI)
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    threads = int(os.environ.get("THREADS", 8))

    logger.info("Starting MetaTrader 5 REST API on %s:%s (threads=%d)", host, port, threads)

    try:
        from waitress import serve
        logger.info("Using Waitress WSGI multi-threaded production server (%d worker threads)", threads)
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            channel_timeout=120,
            cleanup_interval=30,
            ident="MT5-REST-API/1.0",
        )
    except ImportError:
        logger.warning("Waitress not found, using Flask development server")
        app.run(host=host, port=port, debug=False, threaded=True)
