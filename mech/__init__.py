from flask import Flask, jsonify
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
import os
import yaml

from .blueprints.mechanics.routes import mechanics_bp
from .blueprints.service_tickets.routes import service_tickets_bp
from .blueprints.customers.routes import customers_bp
from .blueprints.inventory.routes import inventory_bp
from .extensions import db, ma, limiter, cache, migrate
from .config import DevelopmentConfig, TestingConfig, ProductionConfig

def create_app(config_name="ProductionConfig"):
    app = Flask(__name__, static_folder="static")
    app.url_map.strict_slashes = False
    app.config.from_object(f"mech.config.{config_name}")

    ### Initialize Extensions #####
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    #### Register Blueprints ###
    app.register_blueprint(customers_bp,       url_prefix="/customers")
    app.register_blueprint(mechanics_bp,       url_prefix="/mechanics")
    app.register_blueprint(service_tickets_bp, url_prefix="/service_tickets")
    app.register_blueprint(inventory_bp,       url_prefix="/inventory")

    ####### Auto generate swagger.json #####
    @app.route("/swagger.json")
    def swagger_spec():
        ##### Load static definitions ######
        static_path = os.path.join(app.static_folder, "swagger.yaml")
        with open(static_path, 'r') as f:
            static_docs = yaml.safe_load(f)

        ##### Generate spec ####
        spec = swagger(app)
        spec["info"]["title"] = "MechAPI"
        spec["info"]["version"] = "1.0.0"

        ### Merge components.schemas into Swagger2 definitions #####
        spec.setdefault("definitions", {}).update(
            static_docs.get("components", {}).get("schemas", {})
        )

        return jsonify(spec)

    ###### Serve Swagger UI ###
    swagger_ui_bp = get_swaggerui_blueprint(
        "/docs",
        "/swagger.json",
        config={"app_name": "MechAPI"}
    )
    app.register_blueprint(swagger_ui_bp, url_prefix="/docs")

    return app
