from flask import Flask
from .blueprints.mechanics import mechanics_bp
from .blueprints.service_tickets import service_ticket_bp
from .blueprints.customers import customers_bp
from .extensions import db, ma

def create_app(config_name="development"):
    app = Flask(__name__)
   
    app.config.from_object(f'config.{config_name}')
    db.init_app(app)
    ma.init_app(app)
    app.register_blueprint(mechanics_bp, url_prefix='/mechanics')
    app.register_blueprint(service_ticket_bp, url_prefix='/service-tickets')
    app.register_blueprint(customers_bp, url_prefix='/customers')
    return app