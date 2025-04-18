from datetime import datetime, timedelta, timezone
from jose import jwt
import jose
from functools import wraps
from flask import request, jsonify

SECRET_KEY = "a super secret, secret key"
ALGO = "HS256"

def encode_customer_token(customer_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(customer_id),
        'role': 'customer'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def encode_mechanic_token(mechanic_id):
    payload = {
        'exp': datetime.now(timezone.utc) + timedelta(hours=1),
        'iat': datetime.now(timezone.utc),
        'sub': str(mechanic_id),
        'role': 'mechanic'
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGO)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ### Use same logic to extract and decode ###
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        if data.get('role') != 'customer':
            return jsonify({'message': 'Invalid role'}), 403
        return f(data['sub'], *args, **kwargs)
    return decorated

def mechanic_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2:
                token = parts[1]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        except jose.exceptions.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jose.exceptions.JWTError:
            return jsonify({'message': 'Invalid token!'}), 401

        if data.get('role') != 'mechanic':
            return jsonify({'message': 'Mechanic access required'}), 403

        ### Pass mechanic_id through to the route ###
        return f(data['sub'], *args, **kwargs)
    return decorated