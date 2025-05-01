import functools
import jwt
from jwt import InvalidTokenError
from flask import request, jsonify, current_app
from mech.models import Mechanic
from functools import wraps
import os

SECRET_KEY = os.environ.get('SECRET_KEY') or "super secret secrets"

def encode_mechanic_token(mechanic_id):
    payload = {'sub': str(mechanic_id)}
    key = current_app.config['SECRET_KEY']
    algo = current_app.config.get('JWT_ALGO', 'HS256')
    return jwt.encode(payload, key, algorithm=algo)

def mechanic_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        token = parts[1]
        try:
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=[current_app.config.get('JWT_ALGO', 'HS256')]
            )
        except InvalidTokenError as e:
            return jsonify({'error': 'Invalid token'}), 401
        
        sub = data.get('sub')
        try:
            mech_id = int(sub)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid token payload'}), 401
        
        if not Mechanic.query.get(mech_id):
            return jsonify({'error': 'Invalid token payload'}), 401

        return f(mech_id, *args, **kwargs)

    return wrapper

def encode_customer_token(customer_id):
    payload = {'sub': str(customer_id)}
    key = current_app.config['SECRET_KEY']
    algo = current_app.config.get('JWT_ALGO', 'HS256')
    return jwt.encode(payload, key, algorithm=algo)

def customer_required(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        parts = auth.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401

        token = parts[1]
        try:
            data = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=[current_app.config.get('JWT_ALGO', 'HS256')]
            )
        except InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401

        sub = data.get('sub')
        try:
            cust_id = int(sub)
        except (TypeError, ValueError):
            return jsonify({'error': 'Invalid token payload'}), 401

        if not Customer.query.get(cust_id):
            return jsonify({'error': 'Invalid token payload'}), 401

        return f(cust_id, *args, **kwargs)

    return wrapper