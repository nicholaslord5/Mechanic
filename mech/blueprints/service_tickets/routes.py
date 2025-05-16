from flask import Blueprint, request, jsonify
from datetime import date
from mech.extensions import db
from mech.models import ServiceTicket, Mechanic
from mech.blueprints.service_tickets.schemas import service_ticket_schema, service_tickets_schema
from mech.utils.util import mechanic_required
from mech.blueprints.service_tickets import service_tickets_bp

@service_tickets_bp.route('/', methods=['GET'])
def get_tickets():
    """
    List Service Tickets

    ---
    tags:
      - ServiceTickets
    summary: Retrieve a paginated list of service tickets
    description: Returns service tickets along with pagination metadata.
    parameters:
      - in: query
        name: page
        type: integer
        required: false
        default: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        required: false
        default: 10
        description: Number of tickets per page
    responses:
      200:
        description: A paginated list of service tickets
        schema:
          type: object
          properties:
            tickets:
              type: array
              items:
                $ref: "#/definitions/ServiceTicket"
            meta:
              $ref: "#/definitions/Meta"
        examples:
          application/json:
            tickets:
              - id: 1
                vin: "1HGCM82633A004352"
                service_date: "2025-05-01"
                service_desc: "Oil change"
                customer_id: 1
                mechanics:
                  - id: 2
                    name: "Bob Jones"
            meta:
              page: 1
              per_page: 10
              total: 5
              pages: 1
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    pagination = ServiceTicket.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = pagination.items
    return jsonify({
        'tickets': service_tickets_schema.dump(items),
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200

@service_tickets_bp.route('/', methods=['POST'])
@mechanic_required
def create_ticket(current_mech_id):
    """
    Create Service Ticket

    ---
    tags:
      - ServiceTickets
    summary: Create a new service ticket
    description: Add a service ticket and assign the requesting mechanic automatically.
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: body
        name: ticket
        required: true
        schema:
          $ref: "#/definitions/ServiceTicketCreate"
    responses:
      201:
        description: Service ticket created successfully
        schema:
          $ref: "#/definitions/IdResponse"
        examples:
          application/json:
            id: 100
      400:
        description: Validation error or missing field
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Missing field 'vin'"
    """
    data = request.get_json() or {}
    for field in ('vin', 'service_date', 'service_desc', 'customer_id'):
        if field not in data:
            return jsonify({'error': f"Missing field '{field}'"}), 400

    try:
        service_date_obj = date.fromisoformat(data['service_date'])
    except ValueError:
        return jsonify({'error': "Invalid 'service_date' format (YYYY-MM-DD expected)"}), 400

    ticket = ServiceTicket(
        vin=data['vin'],
        service_date=service_date_obj,
        service_desc=data['service_desc'],
        customer_id=data['customer_id']
    )
    mech = Mechanic.query.get(current_mech_id)
    ticket.mechanics.append(mech)

    db.session.add(ticket)
    db.session.commit()
    return jsonify({'id': ticket.id}), 201

@service_tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@mechanic_required
def update_ticket(current_mech_id, ticket_id):
    """
    Update Service Ticket

    ---
    tags:
      - ServiceTickets
    summary: Update details of a service ticket
    description: Modify one or more fields of a service ticket. Requires mechanic authentication.
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
        name: ticket
        required: true
        schema:
          $ref: "#/definitions/ServiceTicketUpdate"
    responses:
      200:
        description: Updated service ticket
        schema:
          $ref: "#/definitions/ServiceTicket"
        examples:
          application/json:
            id: 100
            vin: "1HGCM82633A004352"
            service_date: "2025-05-02"
            service_desc: "Brake inspection"
            customer_id: 1
            mechanics:
              - id: 3
                name: "Carol Lee"
      400:
        description: Invalid data or date format
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Invalid 'service_date' format (YYYY-MM-DD expected)"
      404:
        description: Ticket not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "ServiceTicket not found"
    """
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    updates = request.get_json() or {}

    if 'service_date' in updates:
        try:
            updates['service_date'] = date.fromisoformat(updates['service_date'])
        except ValueError:
            return jsonify({'error': "Invalid 'service_date' format (YYYY-MM-DD expected)"}), 400

    for key, val in updates.items():
        setattr(ticket, key, val)

    db.session.commit()
    return jsonify(service_ticket_schema.dump(ticket)), 200

@service_tickets_bp.route('/<int:ticket_id>/edit', methods=['PUT'])
@mechanic_required
def edit_ticket_mechanics(current_mech_id, ticket_id):
    """
    Edit Ticket Mechanics

    ---
    tags:
      - ServiceTickets
    summary: Modify mechanics assigned to a service ticket
    description: Add or remove mechanics from a ticket. Requires mechanic authentication.
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
          properties:
            add_ids:
              type: array
              items:
                type: integer
              description: List of mechanic IDs to add
            remove_ids:
              type: array
              items:
                type: integer
              description: List of mechanic IDs to remove
    responses:
      200:
        description: Ticket mechanics updated successfully
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "Ticket mechanics updated successfully"
      404:
        description: Ticket not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "ServiceTicket not found"
    """
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    data = request.get_json() or {}
    add_ids = data.get('add_ids', [])
    remove_ids = data.get('remove_ids', [])

    for m_id in add_ids:
        mech = Mechanic.query.get(m_id)
        if mech and not ticket.mechanics.filter_by(id=m_id).first():
            ticket.mechanics.append(mech)

    for m_id in remove_ids:
        mech = Mechanic.query.get(m_id)
        if mech and ticket.mechanics.filter_by(id=m_id).first():
            ticket.mechanics.remove(mech)

    db.session.commit()
    return jsonify({'message': 'Ticket mechanics updated successfully'}), 200

@service_tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@mechanic_required
def delete_ticket(current_mech_id, ticket_id):
    """
    Delete Service Ticket

    ---
    tags:
      - ServiceTickets
    summary: Delete a service ticket by ID
    description: Remove/delete a ticket. Requires mechanic authentication.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: ticket_id
        required: true
        type: integer
        description: Service Ticket ID
    responses:
      200:
        description: Ticket deletion successful
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "ServiceTicket deleted successfully"
      404:
        description: Ticket not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "ServiceTicket not found"
    """
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'ServiceTicket deleted successfully'}), 200
