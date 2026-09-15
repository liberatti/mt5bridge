import os
import sys
import time
import logging
from flask import Flask, request, g
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from utils.response import make_response
from routes import register_routes

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("flask_app")
access_logger = logging.getLogger("access")


def create_app():
    app = Flask(__name__, template_folder="templates")
    CORS(app)

    # 1. Request Logging Middleware
    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        duration_ms = (time.time() - getattr(g, "start_time", time.time())) * 1000
        ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        query = f"?{request.query_string.decode('utf-8')}" if request.query_string else ""
        access_logger.info(
            "%s - \"%s %s%s %s\" %s %s [%.2fms]",
            ip,
            request.method,
            request.path,
            query,
            request.environ.get("SERVER_PROTOCOL", "HTTP/1.1"),
            response.status_code,
            response.content_length or 0,
            duration_ms,
        )
        return response

    # 2. Global Error handling
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        return make_response(error=e.description, status_code=e.code)

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("API Error: %s", e)
        return make_response(error=str(e), status_code=500)

    # 3. Register all documentation and modular API routes
    register_routes(app)

    # 4. Auto-initialize MetaTrader 5 connection on server startup in background
    def _bg_init():
        try:
            import time
            time.sleep(1)
            from services.base_service import BaseService
            BaseService.ensure_initialized()
        except Exception as e:
            logger.warning("MetaTrader 5 background auto-initialization deferred: %s", e)

    import threading
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
