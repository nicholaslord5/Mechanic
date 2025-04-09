from flask import Blueprint, request, jsonify
from mech.blueprints.service_tickets.schemas import ticket_schema, tickets_schema
from marshmallow import ValidationError
from mech.models import ServiceTicket, db
from sqlalchemy import select

service_tickets_bp = Blueprint('service_tickets', __name__)

@service_tickets_bp.route("/service_tickets", methods=['POST'])
def create_ticket():
    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    new_ticket = ServiceTicket(**ticket_data)
    db.session.add(new_ticket)
    db.session.commit()
    return ticket_schema.jsonify(new_ticket), 201

@service_tickets_bp.route("/service_tickets", methods=['GET'])
def get_tickets():
    tickets = ServiceTicket.query.all()
    return tickets_schema.jsonify(tickets), 200

@service_tickets_bp.route("/service_tickets/<int:id>", methods=['PUT'])
def update_ticket(id):
    ticket = ServiceTicket.query.get(id)
    if not ticket:
        return jsonify({"error": "Service ticket not found"}), 404
    
    ticket_data = request.json
    for key, value in ticket_data.items():
        setattr(ticket, key, value)
    
    db.session.commit()
    return ticket_schema.jsonify(ticket), 200

@service_tickets_bp.route("/service_tickets/<int:id>", methods=['DELETE'])
def delete_ticket(id):
    ticket = ServiceTicket.query.get(id)
    if not ticket:
        return jsonify({"error": "Service ticket not found"}), 404
    
    db.session.delete(ticket)
    db.session.commit()
    return jsonify({"message": "Service ticket deleted successfully"}), 200