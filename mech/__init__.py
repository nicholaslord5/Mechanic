from flask import Flask
from mech.blueprints.mechanics.routes import mechanics_bp
from mech.blueprints.service_tickets.routes import service_tickets_bp
from mech.blueprints.inventory import inventory_bp
from .extensions import db, ma, limiter, cache
from mech.blueprints.customers.routes import customers_bp
from .config import DevelopmentConfig, TestingConfig, ProductionConfig
from flask_swagger_ui import get_swaggerui_blueprint


def create_app(config_name="ProductionConfig"):
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
    SWAGGER_URL = "/docs"
    API_URL = "/static/swagger.yaml"
    swagger_bp  = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={ "app_name": "MechAPI" }
    )
    app.register_blueprint(swagger_bp, url_prefix=SWAGGER_URL)
    return app