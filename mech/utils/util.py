import functools
import jwt
from jwt import InvalidTokenError
from flask import request, jsonify, current_app
from mech.models import Mechanic, Customer
from mech.models import Mechanic, Customer
from functools import wraps
import os
from datetime import datetime, timedelta

SECRET_KEY = os.environ.get('SECRET_KEY') or "super secret secrets"

##### Generate JWT for mechanics ###
def encode_mechanic_token(mechanic_id):
    payload = {'sub': str(mechanic_id)}
    key = current_app.config['SECRET_KEY']
    algo = current_app.config.get('JWT_ALGO', 'HS256')
    return jwt.encode(payload, key, algorithm=algo)

#### ensuer valid mechanic token is present #####
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
        except InvalidTokenError:
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

##### generate JWT for customers authentication####
def encode_customer_token(customer_id):
    payload = {
        'customer_id': customer_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=24)  ### Token expires in 24 hrs ###
    }
    
    token = jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    
    return token

###### ensur a valid customer token is present ######
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

#### Decorator to ensure valid mech/cust JWT is present ######
import jwt
from functools import wraps
from flask import request, jsonify, current_app
from mech.models import Customer

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(' ')[1]  #### Remove "bearer" prefix ###
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        try:
            ####### Decode token using secret key######
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            customer_id = payload['customer_id']  # Adjust this key based on your token structure
            current_user = Customer.query.get(customer_id)
            
            if not current_user:
                return jsonify({'error': 'Invalid token - user not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Pass current_user as the first argument to the wrapped function
        return f(current_user, *args, **kwargs)
    
    return wrapper