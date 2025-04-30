from flask import request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from mech.extensions import db
from mech.models import Mechanic, ServiceTicket
from mech.utils.util import mechanic_required, encode_mechanic_token
from . import mechanics_bp

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
    return jsonify({'auth_token': token}), 200

@mechanics_bp.route('/', methods=['POST'])
def create_mechanic():
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
    mechs = Mechanic.query.all()
    result = [
        {'id': m.id, 'name': m.name, 'email': m.email, 'phone': m.phone, 'salary': m.salary}
        for m in mechs
    ]
    return jsonify(result), 200

@mechanics_bp.route('/ranked', methods=['GET'])
@mechanic_required
def get_mechanics_by_ticket_count(current_mech_id):
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

    # include "added to ticket" so tests pass their substring assertion
    return jsonify({
        'message': f'Mechanic {mech_id} added to ticket {ticket_id}'
    }), 200
