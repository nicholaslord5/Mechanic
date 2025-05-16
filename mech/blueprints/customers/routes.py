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
    """
    Create Customer

    ---
    tags:
      - Customers
    summary: Register a new customer
    description: Create a customer by providing name, email, phone, and password.
    consumes:
      - application/json
    parameters:
      - in: body
        name: customer
        required: true
        schema:
          $ref: "#/definitions/CustomerCreate"
    responses:
      201:
        description: Customer created successfully
        schema:
          $ref: "#/definitions/Customer"
        examples:
          application/json:
            id: 1
            name: "Jane Doe"
            email: "jane@example.com"
            phone: "555-555-1234"
      400:
        description: Validation error
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Invalid input data"
    """
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
    """
    Customer Login

    ---
    tags:
      - Customers
    summary: Authenticate customer and return JWT
    description: Login a customer using email and password to receive a JWT token.
    consumes:
      - application/json
    parameters:
      - in: body
        name: credentials
        required: true
        schema:
          $ref: "#/definitions/CustomerLogin"
    responses:
      200:
        description: Login successful
        schema:
          $ref: "#/definitions/CustomerAuthResponse"
        examples:
          application/json:
            status: "success"
            customer: 1
            auth_token: "eyJhbGciOiJIUzI1NiIs..."
      400:
        description: Missing credentials
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Email & password required"
      401:
        description: Invalid credentials
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Invalid credentials"
    """
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
    """
    List Customers

    ---
    tags:
      - Customers
    summary: Retrieve a paginated list of customers
    description: Returns customers along with pagination metadata.
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
        description: Number of customers per page
    responses:
      200:
        description: A paginated list of customers
        schema:
          type: object
          properties:
            customers:
              type: array
              items:
                $ref: "#/definitions/Customer"
            meta:
              $ref: "#/definitions/Meta"
        examples:
          application/json:
            customers:
              - id: 1
                name: "Jane Doe"
                email: "jane@example.com"
                phone: "555-555-1234"
            meta:
              page: 1
              per_page: 10
              total: 25
              pages: 3
    """
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
    """
    Update Customer

    ---
    tags:
      - Customers
    summary: Update an existing customer
    description: Modify one or more fields of a customer record.
    parameters:
      - in: path
        name: id
        required: true
        type: integer
        description: Customer ID
      - in: body
        name: customer
        required: true
        schema:
          $ref: "#/definitions/CustomerUpdate"
    responses:
      200:
        description: Customer updated successfully
        schema:
          $ref: "#/definitions/Customer"
        examples:
          application/json:
            id: 1
            name: "Jane Doe"
            email: "jane@newemail.com"
            phone: "999-999-9999"
      404:
        description: Customer not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Customer not found"
    """
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
    """
    Delete Current Customer

    ---
    tags:
      - Customers
    summary: Delete the authenticated customer
    description: Delete the customer associated with the provided JWT.
    security:
      - bearerAuth: []
    parameters:
      - in: header
        name: Authorization
        required: true
        type: string
        description: Bearer JWT token
    responses:
      200:
        description: Customer deletion successful
        schema:
          $ref: "#/definitions/MessageResponse"
        examples:
          application/json:
            message: "deleted customer 1"
      401:
        description: Unauthorized or invalid token
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Missing or invalid Authorization header"
      404:
        description: Customer not found
        schema:
          $ref: "#/definitions/ErrorResponse"
        examples:
          application/json:
            error: "Customer not found"
    """
    auth = request.headers.get('Authorization', '')
    if not auth.lower().startswith('bearer '):
        return jsonify({'error': 'Missing or invalid Authorization header'}), 401

    token = auth.split(' ', 1)[1]
    #### parse payload without verifying signature
    try:
        payload_b64 = token.split('.')[1]
        ##### pad base64
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
