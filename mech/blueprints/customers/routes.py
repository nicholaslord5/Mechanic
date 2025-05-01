import base64, json
from flask import Flask
from flask import Blueprint, request, jsonify
from . import customers_bp
from mech.blueprints.customers.schemas import customer_schema, customers_schema
from marshmallow import ValidationError
from mech.models import Customer, db
from sqlalchemy import select, delete
from mech.extensions import cache
from mech.utils.util import encode_customer_token, customer_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, current_app
import jwt
from jwt import InvalidTokenError
from mech.models import Customer, db

@customers_bp.route("/", methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(**customer_data)
    customer_data['password'] = generate_password_hash(customer_data['password'])
    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

@customers_bp.route("/login", methods=['POST'])
def customer_login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email & password required'}), 400

    cust = Customer.query.filter_by(email=email).first()
    if not cust or not check_password_hash(cust.password, password):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = encode_customer_token(cust.id)
    return jsonify({
        'status': 'success',
        'customer': cust.id,
        'auth_token': token
    }), 200

@customers_bp.route("/", methods=['GET'])
def get_customers():
    #### apply pagination to GET customers ####
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    pagination = Customer.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    items = pagination.items

    return jsonify({
        'customers': customers_schema.dump(items),
        'meta': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    }), 200

@customers_bp.route("/<int:id>", methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    customer_data = request.json
    for key, value in customer_data.items():
        setattr(customer, key, value)
    
    db.session.commit()
    return customer_schema.jsonify(customer), 200

@customers_bp.route('/', methods=['DELETE'])
def delete_current_customer():
    auth = request.headers.get('Authorization', '')
    if not auth.lower().startswith('bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401

    token = auth.split(' ', 1)[1]
    # parse payload without verifying signature
    try:
        # JWT is header.payload.signature
        payload_b64 = token.split('.')[1]
        # pad base64 if needed
        padding = '=' * (-len(payload_b64) % 4)
        payload_b64 += padding
        data = json.loads(base64.urlsafe_b64decode(payload_b64).decode())
    except Exception:
        return jsonify({'error': 'Invalid token'}), 401

    current_customer_id = data.get('sub')
    if not current_customer_id:
        return jsonify({'error': 'Invalid token'}), 401

    customer = Customer.query.get(current_customer_id)
    if not customer:
        return jsonify({'error': 'Customer not found'}), 404

    db.session.delete(customer)
    db.session.commit()
    return jsonify({'message': f'deleted customer {current_customer_id}'}), 200