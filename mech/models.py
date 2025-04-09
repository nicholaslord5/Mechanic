from .extensions import db
from sqlalchemy import ForeignKey
from datetime import date

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)


class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(17), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_desc = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, ForeignKey("customers.id"))


class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    salary = db.Column(db.Integer, nullable=False)


class ServiceMechanics(db.Model):
    __tablename__ = "service_mechanics"

    ticket_id = db.Column(db.Integer, ForeignKey("service_tickets.id"), primary_key=True)
    mechanic_id = db.Column(db.Integer, ForeignKey("mechanics.id"), primary_key=True)