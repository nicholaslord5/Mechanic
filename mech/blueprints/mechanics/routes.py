from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, desc
from marshmallow import ValidationError
from mech.extensions import db
from mech.utils.util import encode_mechanic_token, mechanic_required
from mech.models import Mechanic, ServiceTicket, service_mechanics
from mech.blueprints.mechanics.schemas import mechanic_schema, mechanics_schema

mechanics_bp = Blueprint('mechanics', __name__, url_prefix='/mechanics')

@mechanics_bp.route('/login', methods=['POST'])
def mechanic_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email & password required'}), 400

    mech = Mechanic.query.filter_by(email=email).first()
    if not mech or not check_password_hash(mech.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = encode_mechanic_token(mech.id)
    return jsonify({
        'status': 'success',
        'mechanic': mech.id,
        'auth_token': token
    }), 200

@mechanics_bp.route('/', methods=['POST'])
def create_mechanic():
    if not request.is_json:
        return jsonify({'error': 'Expected JSON'}), 400
    try:
        data = mechanic_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400

    data['password'] = generate_password_hash(data['password'])
    new_mech = Mechanic(**data)
    db.session.add(new_mech)
    db.session.commit()

    return mechanic_schema.jsonify(new_mech), 201

@mechanics_bp.route('/', methods=['GET'])
def get_mechanics():
    mechanics = Mechanic.query.all()
    return mechanics_schema.jsonify(mechanics), 200

@mechanics_bp.route('/ranked', methods=['GET'])
@mechanic_required
def get_mechanics_by_ticket_count(current_mech_id):
    counts = (
        db.session.query(
            Mechanic,
            func.count(service_mechanics.c.ticket_id).label('ticket_count')
        )
        .outerjoin(service_mechanics, Mechanic.id == service_mechanics.c.mechanic_id)
        .group_by(Mechanic.id)
        .order_by(desc('ticket_count'))
        .all()
    )

    result = []
    for mech, ticket_count in counts:
        result.append({
            'id': mech.id,
            'name': mech.name,
            'email': mech.email,
            'phone': mech.phone,
            'salary': mech.salary,
            'ticket_count': ticket_count
        })

    return jsonify(result), 200

@mechanics_bp.route('/<int:mech_id>/tickets/<int:ticket_id>', methods=['POST'])
@mechanic_required
def add_mechanic_to_ticket(current_mech_id, mech_id, ticket_id):
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404

    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404
    if ticket in mech.tickets:
        return jsonify({'message': 'Already assigned'}), 200

    mech.tickets.append(ticket)
    db.session.commit()
    return jsonify({
        'message': f'Mechanic {mech.id} added to ticket {ticket.id}'
    }), 200

@mechanics_bp.route('/<int:mech_id>', methods=['PUT'])
@mechanic_required
def update_mechanic(current_mech_id, mech_id):
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404
    if not request.is_json:
        return jsonify({'error': 'Expected JSON'}), 400
    try:
        data = mechanic_schema.load(request.get_json(), partial=True)
    except ValidationError as err:
        return jsonify(err.messages), 400
    for key, value in data.items():
        setattr(mech, key, value)
    db.session.commit()
    return mechanic_schema.jsonify(mech), 200

@mechanics_bp.route('/<int:mech_id>', methods=['DELETE'])
@mechanic_required
def delete_mechanic(current_mech_id, mech_id):
    mech = Mechanic.query.get(mech_id)
    if not mech:
        return jsonify({'error': 'Mechanic not found'}), 404
    db.session.delete(mech)
    db.session.commit()
    return jsonify({'message': 'Mechanic deleted successfully'}), 200
