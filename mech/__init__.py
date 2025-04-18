from flask import Flask
from .blueprints.mechanics.routes import mechanics_bp
from .blueprints.service_tickets.routes import service_tickets_bp
from .blueprints.customers import customers_bp
from .blueprints.inventory import inventory_bp
from .extensions import db, ma, limiter, cache

def create_app(config_name="development"):
    app = Flask(__name__)
   
    app.config.from_object(f'config.{config_name}')
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    return app