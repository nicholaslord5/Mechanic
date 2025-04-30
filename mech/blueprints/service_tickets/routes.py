from flask import Blueprint, request, jsonify
from datetime import date
from mech.extensions import db
from mech.models import ServiceTicket, Mechanic
from mech.blueprints.service_tickets.schemas import service_ticket_schema, service_tickets_schema
from mech.utils.util import mechanic_required, SECRET_KEY, JWT_ALGO
from mech.blueprints.service_tickets import service_tickets_bp

@service_tickets_bp.route('/', methods=['GET'])
def get_tickets():
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
    data = request.get_json() or {}
    for field in ('vin', 'service_date', 'service_desc', 'customer_id'):
        if field not in data:
            return jsonify({'error': f"Missing field '{field}'"}), 400

    ###### parse ISO-date string into a Python date object
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
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    updates = request.get_json() or {}

    ###### if client supplied a new date string, convert it
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
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    data = request.get_json() or {}
    add_ids = data.get('add_ids', [])
    remove_ids = data.get('remove_ids', [])

    ###### add mechanics
    for m_id in add_ids:
        mech = Mechanic.query.get(m_id)
        if mech and not ticket.mechanics.filter_by(id=m_id).first():
            ticket.mechanics.append(mech)

    ##### remove mechanics
    for m_id in remove_ids:
        mech = Mechanic.query.get(m_id)
        if mech and ticket.mechanics.filter_by(id=m_id).first():
            ticket.mechanics.remove(mech)

    db.session.commit()
    return jsonify({'message': 'Ticket mechanics updated successfully'}), 200

@service_tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@mechanic_required
def delete_ticket(current_mech_id, ticket_id):
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'ServiceTicket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'ServiceTicket deleted successfully'}), 200
