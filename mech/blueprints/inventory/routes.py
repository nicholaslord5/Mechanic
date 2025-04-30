from flask import Flask
from flask import Blueprint, request, jsonify
from mech.models import Inventory, ServiceTicket, db
from mech.blueprints.inventory.schemas import inventory_schema, inventories_schema
from mech.utils.util import mechanic_required
from . import inventory_bp

@inventory_bp.route("/", methods=['POST'])
@mechanic_required
def create_part(mech_id):
    data = request.get_json() or {}
    part = Inventory(**data)
    db.session.add(part)
    db.session.commit()
    return inventory_schema.jsonify(part), 201

@inventory_bp.route("/", methods=['GET'])
def get_parts():
    parts = Inventory.query.all()
    return inventories_schema.jsonify(parts), 200

@inventory_bp.route("/<int:id>", methods=['PUT'])
@mechanic_required
def update_part(mech_id, id):
    part = Inventory.query.get(id)
    if not part:
        return jsonify({"error":"Part not found"}), 404
    for k,v in request.json.items():
        setattr(part, k, v)
    db.session.commit()
    return inventory_schema.jsonify(part), 200

@inventory_bp.route("/<int:id>", methods=['DELETE'])
@mechanic_required
def delete_part(mech_id, id):
    part = Inventory.query.get(id)
    if not part:
        return jsonify({"error":"Part not found"}), 404
    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

### Add part to a ticket ###
@inventory_bp.route("/<int:ticket_id>/add_part", methods=['POST'])
@mechanic_required
def add_part_to_ticket(mech_id, ticket_id):
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({"error":"Ticket not found"}), 404
    part_id = request.json.get("part_id")
    part = Inventory.query.get(part_id)
    if not part:
        return jsonify({"error":"Part not found"}), 404
    if part not in ticket.parts:
        ticket.parts.append(part)
        db.session.commit()
    return jsonify({"message": f"Part {part_id} added to ticket {ticket_id}"}), 200
