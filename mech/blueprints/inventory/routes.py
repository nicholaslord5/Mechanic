from flask import Blueprint, request, jsonify
from mech.models import Inventory, ServiceTicket, db
from mech.blueprints.inventory.schemas import inventory_schema, inventories_schema
from mech.utils.util import mechanic_required
from . import inventory_bp

@inventory_bp.route("/", methods=['POST'])
@mechanic_required
def create_part(mech_id):
    """
    Create Part

    ---
    tags:
      - Inventory
    summary: Create a new inventory part
    description: Add a new part to the inventory. Requires mechanic authentication.
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: part
        required: true
        schema:
          $ref: "#/definitions/InventoryCreate"
    responses:
      201:
        description: Part created successfully
        schema:
          $ref: "#/definitions/Inventory"
        examples:
          application/json:
            id: 5
            name: "Brake Pad"
            price: 9.99
      400:
        description: Validation error
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Missing required field 'name'"
    """
    data = request.get_json() or {}
    part = Inventory(**data)
    db.session.add(part)
    db.session.commit()
    return inventory_schema.jsonify(part), 201

@inventory_bp.route("/", methods=['GET'])
def get_parts():
    """
    List Parts

    ---
    tags:
      - Inventory
    summary: Retrieve all inventory parts
    description: Returns a list of all parts in the inventory.
    responses:
      200:
        description: List of parts
        schema:
          type: array
          items:
            $ref: "#/definitions/Inventory"
        examples:
          application/json:
            - id: 1
              name: "Brake Pad"
              price: 9.99
            - id: 2
              name: "Oil Filter"
              price: 5.49
    """
    parts = Inventory.query.all()
    return inventories_schema.jsonify(parts), 200

@inventory_bp.route("/<int:id>", methods=['PUT'])
@mechanic_required
def update_part(mech_id, id):
    """
    Update Part

    ---
    tags:
      - Inventory
    summary: Update an existing part
    description: Modify the attributes of an inventory part such as name or price. Requires mechanic authentication.
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: id
        required: true
        type: integer
        description: Part ID
      - in: body
        name: part
        required: true
        schema:
          $ref: "#/definitions/InventoryUpdate"
    responses:
      200:
        description: Part updated successfully
        schema:
          $ref: "#/definitions/Inventory"
        examples:
          application/json:
            id: 5
            name: "Brake Pad"
            price: 12.99
      400:
        description: Validation error
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Invalid price value"
      404:
        description: Part not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Part not found"
    """
    part = Inventory.query.get(id)
    if not part:
        return jsonify({"error":"Part not found"}), 404
    for k, v in request.json.items():
        setattr(part, k, v)
    db.session.commit()
    return inventory_schema.jsonify(part), 200

@inventory_bp.route("/<int:id>", methods=['DELETE'])
@mechanic_required
def delete_part(mech_id, id):
    """
    Delete Part

    ---
    tags:
      - Inventory
    summary: Delete a part by ID
    description: Remove a part from the inventory. Requires mechanic authentication.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        type: integer
        description: Part ID
    responses:
      200:
        description: Part deletion successful
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "Deleted"
      401:
        description: Unauthorized
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      404:
        description: Part not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Part not found"
    """
    part = Inventory.query.get(id)
    if not part:
        return jsonify({"error":"Part not found"}), 404
    db.session.delete(part)
    db.session.commit()
    return jsonify({"message": "Deleted"}), 200

@inventory_bp.route("/<int:ticket_id>/add_part", methods=['POST'])
@mechanic_required
def add_part_to_ticket(mech_id, ticket_id):
    """
    Add Part to Ticket

    ---
    tags:
      - Inventory
      - ServiceTickets
    summary: Associate a part with a service ticket
    description: Add a specific part to an existing service ticket. Requires mechanic authentication.
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: ticket_id
        required: true
        type: integer
        description: Service Ticket ID
      - in: body
        name: payload
        required: true
        schema:
          type: object
          required:
            - part_id
          properties:
            part_id:
              type: integer
              example: 5
    responses:
      200:
        description: Part added to ticket successfully
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "Part 5 added to ticket 42"
      404:
        description: Ticket or part not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Ticket not found"
    """
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
