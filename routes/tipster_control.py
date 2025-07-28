from flask import Blueprint, request, jsonify
from auth_helpers import token_required
from extensions import db
from models import User, TipsterAccess

from flasgger.utils import swag_from

tipster_control_bp = Blueprint('tipster_control', __name__)

@tipster_control_bp.route('/tips/access', methods=['GET'])
@token_required
@swag_from({
    'tags': ['Tipster Access'],
    'responses': {
        200: {
            'description': 'List of users with access to tipster tips'
        },
        403: {
            'description': 'Unauthorized'
        }
    }
})
def get_tipster_access(current_user):
    if not current_user.is_tipster:
        return jsonify({"error": "Unauthorized"}), 403

    access_records = TipsterAccess.query.filter_by(tipster_id=current_user.id).all()
    result = [
        {
            "user_id": access.user.id,
            "email": access.user.email,
            "first_name": access.user.first_name,
            "last_name": access.user.last_name
        }
        for access in access_records
    ]
    return jsonify(result)


@tipster_control_bp.route('/tips/access/grant', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Tipster Access'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer'}
                },
                'required': ['user_id']
            }
        }
    ],
    'responses': {
        200: {'description': 'Access granted or already exists'},
        403: {'description': 'Unauthorized'},
        400: {'description': 'Missing user_id'}
    }
})
def grant_tip_access(current_user):
    if not current_user.is_tipster:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    existing = TipsterAccess.query.filter_by(tipster_id=current_user.id, user_id=user_id).first()
    if existing:
        return jsonify({"message": "User already has access"}), 200

    db.session.add(TipsterAccess(tipster_id=current_user.id, user_id=user_id))
    db.session.commit()
    return jsonify({"message": "Access granted"})


@tipster_control_bp.route('/tips/access/revoke', methods=['POST'])
@token_required
@swag_from({
    'tags': ['Tipster Access'],
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'integer'}
                },
                'required': ['user_id']
            }
        }
    ],
    'responses': {
        200: {'description': 'Access revoked or not found'},
        403: {'description': 'Unauthorized'},
        400: {'description': 'Missing user_id'}
    }
})
def revoke_tip_access(current_user):
    if not current_user.is_tipster:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    access = TipsterAccess.query.filter_by(tipster_id=current_user.id, user_id=user_id).first()
    if not access:
        return jsonify({"message": "User did not have access"}), 200

    db.session.delete(access)
    db.session.commit()
    return jsonify({"message": "Access revoked"})
