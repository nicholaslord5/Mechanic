from flask import request, jsonify
from . import mechanics_bp
from .schemas import mechanic_schema, mechanics_schema
from ...extensions import db
from ...models import Mechanic
from marshmallow import ValidationError

@mechanics_bp.route("/", methods=['POST'])
def create_mechanic():
    if not request.json:
        return jsonify({"error": "No data provided"}), 400
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    new_mechanic = Mechanic(**mechanic_data)
    db.session.add(new_mechanic)
    db.session.commit()
    return mechanic_schema.jsonify(new_mechanic), 201

@mechanics_bp.route("/", methods=['GET'])
def get_mechanics():
    mechanics = Mechanic.query.all()
    return mechanics_schema.jsonify(mechanics), 200

@mechanics_bp.route("/<int:id>", methods=['PUT'])
def update_mechanic(id):
    mechanic = Mechanic.query.get(id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    if not request.json:
        return jsonify({"error": "No data provided"}), 400
    try:
        mechanic_data = mechanic_schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify(e.messages), 400
    for key, value in mechanic_data.items():
        setattr(mechanic, key, value)
    db.session.commit()
    return mechanic_schema.jsonify(mechanic), 200

@mechanics_bp.route("/<int:id>", methods=['DELETE'])
def delete_mechanic(id):
    mechanic = Mechanic.query.get(id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    db.session.delete(mechanic)
    db.session.commit()
    return jsonify({"message": "Mechanic deleted successfully"}), 200