from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from extensions import db, limiter
import jwt
import datetime
import os
from flasgger.utils import swag_from

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'},
                    'role': {'type': 'string', 'enum': ['tipster', 'follower', 'admin']}
                },
                'required': ['email', 'password', 'role']
            }
        }
    ],
    'responses': {
        200: {'description': 'User registered successfully'},
        409: {'description': 'Email already exists'}
    }
})
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('email', 'password', 'role')):
        return jsonify({'error': 'Missing data'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    hashed_pw = generate_password_hash(data['password'])
    new_user = User(email=data['email'], password=hashed_pw, role=data['role'])

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'})

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
@swag_from({
    'tags': ['Auth'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'email': {'type': 'string'},
                    'password': {'type': 'string'}
                },
                'required': ['email', 'password']
            }
        }
    ],
    'responses': {
        200: {'description': 'JWT token returned'},
        401: {'description': 'Invalid credentials'}
    }
})
def login():
    data = request.get_json()
    if not data or not all(k in data for k in ('email', 'password')):
        return jsonify({'error': 'Missing credentials'}), 400

    user = User.query.filter_by(email=data['email']).first()
    if not user or not check_password_hash(user.password, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, os.getenv('SECRET_KEY'), algorithm='HS256')

    return jsonify({'token': token})
