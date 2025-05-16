from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from mech.extensions import db
from mech.models import Mechanic, ServiceTicket
from mech.utils.util import mechanic_required, encode_mechanic_token
from . import mechanics_bp

@mechanics_bp.route('/login', methods=['POST'])
def mechanic_login():
    """
    Mechanic Login

    ---
    tags:
      - Mechanics
    summary: Authenticate mechanic and return JWT
    description: Login a mechanic using email and password to receive a JWT token.
    consumes:
      - application/json
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          $ref: "#/definitions/MechanicLogin"
    responses:
      200:
        description: Login successful
        schema:
          $ref: "#/definitions/MechanicAuthResponse"
        examples:
          application/json:
            auth_token: "eehaerKHIEYIRKkewhre..."
      400:
        description: Missing credentials
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            message: "Email & password required"
      401:
        description: Invalid credentials
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            message: "Invalid credentials"
    """
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'message': 'Email & password required'}), 400

    mech = Mechanic.query.filter_by(email=email).first()
    if not mech or not check_password_hash(mech.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = encode_mechanic_token(mech.id)
    return jsonify({'auth_token': token}), 200

@mechanics_bp.route('/', methods=['POST'])
def create_mechanic():
    """
    Create Mechanic

    ---
    tags:
      - Mechanics
    summary: Register a new mechanic
    description: Add a mechanic by providing name, email, phone, salary, and password.
    consumes:
      - application/json
    parameters:
      - in: body
        name: mechanic
        required: true
        schema:
          $ref: "#/definitions/MechanicCreate"
    responses:
      201:
        description: Mechanic created successfully
        schema:
          $ref: "#/definitions/IdResponse"
        examples:
          application/json:
            id: 42
      400:
        description: Missing fields
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            message: "Missing fields"
    """
    data = request.get_json() or {}
    required = ['name', 'email', 'phone', 'salary', 'password']
    if not all(field in data for field in required):
        return jsonify({'message': 'Missing fields'}), 400

    mech = Mechanic(
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        salary=data['salary'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(mech)
    db.session.commit()
    return jsonify({'id': mech.id}), 201

@mechanics_bp.route('/', methods=['GET'])
def get_mechanics():
    """
    List Mechanics

    ---
    tags:
      - Mechanics
    summary: Retrieve all mechanics
    description: Returns a list of all mechanics.
    responses:
      200:
        description: List of mechanics
        schema:
          type: array
          items:
            $ref: "#/definitions/Mechanic"
        examples:
          application/json:
            - id: 1
              name: "Joe"
              email: "joe@mech.com"
              phone: "555-555-0001"
              salary: 55000
            - id: 2
              name: "Ann"
              email: "ann@mech.com"
              phone: "555-555-0002"
              salary: 60000
    """
    mechs = Mechanic.query.all()
    result = [
        {'id': m.id, 'name': m.name, 'email': m.email, 'phone': m.phone, 'salary': m.salary}
        for m in mechs
    ]
    return jsonify(result), 200

@mechanics_bp.route('/ranked', methods=['GET'])
@mechanic_required
def get_mechanics_by_ticket_count(current_mech_id):
    """
    List Mechanics by Ticket Count

    ---
    tags:
      - Mechanics
    summary: Retrieve mechanics ranked by number of assigned tickets
    description: Returns mechanics sorted descending by how many service tickets they have.
    security:
      - bearerAuth: []
    responses:
      200:
        description: Ranked list of mechanics
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              ticket_count:
                type: integer
        examples:
          application/json:
            - id: 2
              name: "Ann"
              ticket_count: 10
            - id: 1
              name: "Joe"
              ticket_count: 7
    """
    mechs = Mechanic.query.all()
    ranked = []
    for m in mechs:
        ranked.append({
            'id': m.id,
            'name': m.name,
            'ticket_count': m.service_tickets.count()
        })
    ranked.sort(key=lambda x: x['ticket_count'], reverse=True)
    return jsonify(ranked), 200

@mechanics_bp.route('/<int:mech_id>', methods=['PUT'])
@mechanic_required
def update_mechanic(current_mech_id, mech_id):
    """
    Update Mechanic

    ---
    tags:
      - Mechanics
    summary: Update an existing mechanic’s details
    description: Modify one or more fields (including password) of a mechanic record.
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: mech_id
        required: true
        type: integer
        description: Mechanic ID
      - in: body
        name: mechanic
        required: true
        schema:
          $ref: "#/definitions/MechanicUpdate"
    responses:
      200:
        description: Mechanic updated successfully
        schema:
          $ref: "#/definitions/Mechanic"
        examples:
          application/json:
            id: 1
            name: "Joe"
            email: "joe@new.com"
            phone: "555-1111"
            salary: 58000
      403:
        description: Forbidden (cannot modify other mechanics)
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Forbidden"
      404:
        description: Mechanic not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Mechanic not found"
    """
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404
    if current_mech_id != mech_id:
        return jsonify({'error': 'Forbidden'}), 403

    data = request.get_json() or {}
    for key, val in data.items():
        if key == 'password':
            mech.password = generate_password_hash(val)
        else:
            setattr(mech, key, val)
    db.session.commit()

    return jsonify({
        'id': mech.id,
        'name': mech.name,
        'email': mech.email,
        'phone': mech.phone,
        'salary': mech.salary
    }), 200

@mechanics_bp.route('/<int:mech_id>', methods=['DELETE'])
@mechanic_required
def delete_mechanic(current_mech_id, mech_id):
    """
    Delete Mechanic

    ---
    tags:
      - Mechanics
    summary: Delete a mechanic by ID
    description: Remove a mechanic record from the system.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: mech_id
        required: true
        type: integer
        description: Mechanic ID
    responses:
      200:
        description: Mechanic deleted successfully
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "Mechanic deleted successfully"
      403:
        description: Forbidden (cannot delete other mechanics)
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Forbidden"
      404:
        description: Mechanic not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Mechanic not found"
    """
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404
    if current_mech_id != mech_id:
        return jsonify({'error': 'Forbidden'}), 403

    db.session.delete(mech)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted successfully'}), 200

@mechanics_bp.route('/<int:mech_id>/tickets/<int:ticket_id>', methods=['POST'])
@mechanic_required
def assign_ticket(current_mech_id, mech_id, ticket_id):
    """
    Assign Ticket

    ---
    tags:
      - Mechanics
      - ServiceTickets
    summary: Assign a mechanic to a service ticket
    description: Associate a mechanic with an existing service ticket. Requires mechanic authentication.
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: mech_id
        required: true
        type: integer
        description: Mechanic ID
      - in: path
        name: ticket_id
        required: true
        type: integer
        description: Service Ticket ID
    responses:
      200:
        description: Mechanic assigned to ticket successfully
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "Mechanic 1 added to ticket 42"
      403:
        description: Forbidden (cannot assign others)
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Forbidden"
      404:
        description: Mechanic or ticket not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Mechanic not found"
    """
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404

    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    if current_mech_id != mech_id:
        return jsonify({'error': 'Forbidden'}), 403

    if not ticket.mechanics.filter_by(id=mech_id).first():
        ticket.mechanics.append(mech)
        db.session.commit()

    return jsonify({
        'message': f'Mechanic {mech_id} added to ticket {ticket_id}'
    }), 200
