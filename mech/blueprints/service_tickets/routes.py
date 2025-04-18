from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from mech.extensions import db, cache, limiter
from mech.utils.util import mechanic_required
from mech.models import ServiceTicket, Mechanic
from mech.blueprints.service_tickets.schemas import ticket_schema, tickets_schema

service_tickets_bp = Blueprint(
    'service_tickets', __name__, url_prefix='/service_tickets'
)

@service_tickets_bp.route('/', methods=['POST'])
@mechanic_required
@limiter.limit('5 per hour')
def create_ticket(current_mech_id):
    if not request.is_json:
        return jsonify({'error': 'Expected JSON'}), 400
    try:
        data = ticket_schema.load(request.get_json())
    except ValidationError as err:
        return jsonify(err.messages), 400
    new_ticket = ServiceTicket(**data)
    db.session.add(new_ticket)
    db.session.commit()
    return ticket_schema.jsonify(new_ticket), 201

@service_tickets_bp.route('/', methods=['GET'])
@cache.cached(timeout=120)
def get_tickets():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    pagination = ServiceTicket.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = pagination.items
    return jsonify({
        'tickets': tickets_schema.dump(items),
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200

@service_tickets_bp.route('/test', methods=['GET'])
def test_route():
    return jsonify({'message': 'Blueprint is working'}), 200

@service_tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
@mechanic_required
def update_ticket(current_mech_id, ticket_id):
    if not request.is_json:
        return jsonify({'error': 'Expected JSON'}), 400

    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404

    for key, value in request.get_json().items():
        setattr(ticket, key, value)
    db.session.commit()
    return ticket_schema.jsonify(ticket), 200

@service_tickets_bp.route('/<int:ticket_id>/edit', methods=['PUT'])
@mechanic_required
def edit_ticket_mechanics(current_mech_id, ticket_id):
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404

    data = request.get_json() or {}
    remove_ids = data.get('remove_ids', [])
    add_ids = data.get('add_ids', [])

    for mech_id in remove_ids:
        mech = Mechanic.query.get(mech_id)
        if mech in ticket.mechanics:
            ticket.mechanics.remove(mech)

    for mech_id in add_ids:
        mech = Mechanic.query.get(mech_id)
        if mech and mech not in ticket.mechanics:
            ticket.mechanics.append(mech)

    db.session.commit()
    return ticket_schema.jsonify(ticket), 200

@service_tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
@mechanic_required
def delete_ticket(current_mech_id, ticket_id):
    ticket = ServiceTicket.query.get(ticket_id)
    if not ticket:
        return jsonify({'error': 'Service ticket not found'}), 404

    db.session.delete(ticket)
    db.session.commit()
    return jsonify({'message': 'Service ticket deleted successfully'}), 200