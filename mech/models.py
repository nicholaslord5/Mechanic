from .extensions import db
from sqlalchemy import Table, Column, Integer, ForeignKey, String, Date
from sqlalchemy.orm import relationship
from datetime import date

service_mechanics = Table(
    "service_mechanics",
    db.metadata,
    Column("ticket_id", Integer, ForeignKey("service_tickets.id"), primary_key=True),
    Column("mechanic_id", Integer, ForeignKey("mechanics.id"), primary_key=True)
)

service_parts = Table(
    "service_parts",
    db.metadata,
    Column("ticket_id", Integer, ForeignKey("service_tickets.id"), primary_key=True),
    Column("part_id", Integer, ForeignKey("inventory.id"), primary_key=True)
)

class Inventory(db.Model):
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    tickets = relationship(
        "ServiceTicket",
        secondary=service_parts,
        back_populates="parts",
        lazy="dynamic"
    )

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)

    tickets = relationship(
        "ServiceTicket",
        back_populates="customer",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id = db.Column(db.Integer, primary_key=True)
    vin = db.Column(db.String(17), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_desc = db.Column(db.String(255), nullable=False)
    customer_id = db.Column(db.Integer, ForeignKey("customers.id"), nullable=False)

    customer = relationship("Customer", back_populates="tickets")

    # Updated relationship name to match Mechanic.service_tickets
    mechanics = relationship(
        "Mechanic",
        secondary=service_mechanics,
        back_populates="service_tickets",
        lazy="dynamic"
    )
    parts = relationship(
        "Inventory",
        secondary=service_parts,
        back_populates="tickets",
        lazy="dynamic"
    )

class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    salary = db.Column(db.Integer, nullable=False)

    # Renamed relationship to service_tickets to match route logic
    service_tickets = relationship(
        "ServiceTicket",
        secondary=service_mechanics,
        back_populates="mechanics",
        lazy="dynamic"
    )
