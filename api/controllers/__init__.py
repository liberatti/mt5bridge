from controllers.system_controller import system_bp
from controllers.symbols_controller import symbols_bp
from controllers.market_data_controller import market_data_bp
from controllers.trade_controller import trade_bp
from controllers.history_controller import history_bp


def register_blueprints(app):
    """
    Registers all modular Flask Blueprints.
    """
    app.register_blueprint(system_bp, url_prefix="/api")
    app.register_blueprint(symbols_bp, url_prefix="/api")
    app.register_blueprint(market_data_bp, url_prefix="/api")
    app.register_blueprint(trade_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")
