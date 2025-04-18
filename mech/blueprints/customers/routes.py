from flask import Flask
from flask import Blueprint, request, jsonify
from . import customers_bp
from mech.blueprints.customers.schemas import customer_schema, customers_schema
from marshmallow import ValidationError
from mech.models import Customer, db
from sqlalchemy import select, delete
from mech.extensions import cache
from mech.utils.util import encode_customer_token, token_required
from werkzeug.security import generate_password_hash, check_password_hash


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
def login():
    try:
        credentials = request.json
        username = credentials['email']
        password = credentials['password']
    except KeyError:
        return jsonify({'messages': 'Invalid, expecting username and password'}), 400
    
    user = db.session.execute(
        select(Customer).where(Customer.email == email)
    ).scalar_one_or_none()
    user = Customer.query/filter_by(email=email).first()

    if user and user.password == password:
        auth_token = encode_customer_token(user.id)

        return jsonify({
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token
        }), 200
    else:
        return jsonify({'messages': "invalid email or password"}), 401

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

### Apply pagination to GET customers route ###

@customers_bp.route('/', methods=['DELETE'])
@token_required
def delete_customer(customer_id):
    query = select(Customer).where(Customer.id == customer_id)
    user = db.session.execute(query).scalars().first()

    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f"succesfully deleted customer {customer_id}"})