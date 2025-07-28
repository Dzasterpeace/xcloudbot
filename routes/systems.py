from flask import Blueprint, request, jsonify
from extensions import db
from models import System
from auth_helpers import token_required

systems_bp = Blueprint('systems', __name__)

@systems_bp.route('/create', methods=['POST'])
@token_required
def create_system(current_user):
    """
    ---
    tags:
      - Systems
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - stake
            - bank
            - strategy
          properties:
            name:
              type: string
            stake:
              type: number
            bank:
              type: number
            strategy:
              type: string
            description:
              type: string
    responses:
      201:
        description: System created successfully
      400:
        description: Missing fields
    """
    data = request.json
    required_fields = ['name', 'stake', 'bank', 'strategy']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields'}), 400

    new_system = System(
        name=data['name'],
        stake=data['stake'],
        bank=data['bank'],
        strategy=data['strategy'],
        description=data.get('description', ''),
        user_id=current_user.id
    )
    db.session.add(new_system)
    db.session.commit()
    return jsonify({'message': 'System created successfully'}), 201

@systems_bp.route('/', methods=['GET'])
@token_required
def list_systems(current_user):
    """
    ---
    tags:
      - Systems
    responses:
      200:
        description: List all systems for current user
    """
    systems = System.query.filter_by(user_id=current_user.id).all()
    return jsonify([
        {
            'id': s.id,
            'name': s.name,
            'stake': s.stake,
            'bank': s.bank,
            'strategy': s.strategy,
            'description': s.description
        } for s in systems
    ])

@systems_bp.route('/<int:system_id>', methods=['GET'])
@token_required
def get_system(current_user, system_id):
    """
    ---
    tags:
      - Systems
    parameters:
      - name: system_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Get details of a specific system
      404:
        description: System not found
    """
    system = System.query.filter_by(id=system_id, user_id=current_user.id).first()
    if not system:
        return jsonify({'error': 'System not found'}), 404
    return jsonify({
        'id': system.id,
        'name': system.name,
        'stake': system.stake,
        'bank': system.bank,
        'strategy': system.strategy,
        'description': system.description
    })

@systems_bp.route('/<int:system_id>/update', methods=['PUT'])
@token_required
def update_system(current_user, system_id):
    """
    ---
    tags:
      - Systems
    parameters:
      - name: system_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            stake:
              type: number
            bank:
              type: number
            strategy:
              type: string
            description:
              type: string
    responses:
      200:
        description: System updated successfully
      404:
        description: System not found
    """
    system = System.query.filter_by(id=system_id, user_id=current_user.id).first()
    if not system:
        return jsonify({'error': 'System not found'}), 404

    data = request.json
    for field in ['name', 'stake', 'bank', 'strategy', 'description']:
        if field in data:
            setattr(system, field, data[field])
    db.session.commit()
    return jsonify({'message': 'System updated successfully'})

@systems_bp.route('/<int:system_id>/delete', methods=['DELETE'])
@token_required
def delete_system(current_user, system_id):
    """
    ---
    tags:
      - Systems
    parameters:
      - name: system_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: System deleted successfully
      404:
        description: System not found
    """
    system = System.query.filter_by(id=system_id, user_id=current_user.id).first()
    if not system:
        return jsonify({'error': 'System not found'}), 404

    db.session.delete(system)
    db.session.commit()
    return jsonify({'message': 'System deleted successfully'})
