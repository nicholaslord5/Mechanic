from flask import Flask
from mech.blueprints.mechanics.routes import mechanics_bp
from mech.blueprints.service_tickets.routes import service_tickets_bp
from mech.blueprints.inventory import inventory_bp
from .extensions import db, ma, limiter, cache
from mech.blueprints.customers.routes import customers_bp
from .config import DevelopmentConfig, TestingConfig, ProductionConfig

def create_app(config_name="DevelopmentConfig"):
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(f'mech.config.{config_name}')
    db.init_app(app)
    from mech.extensions import migrate
    migrate.init_app(app, db)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_tickets_bp, url_prefix='/service_tickets')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    return app