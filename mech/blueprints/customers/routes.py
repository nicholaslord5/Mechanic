from flask import Flask
from flask import Blueprint, request, jsonify
from . import customers_bp
from mech.blueprints.customers.schemas import customer_schema, customers_schema
from marshmallow import ValidationError
from mech.models import Customer, db
from sqlalchemy import select, delete

@customers_bp.route("/", methods=['POST'])
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400

    new_customer = Customer(**customer_data)
    db.session.add(new_customer)
    db.session.commit()
    return customer_schema.jsonify(new_customer), 201

@customers_bp.route("/", methods=['GET'])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers), 200

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

@customers_bp.route("/<int:id>", methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get(id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted successfully"}),