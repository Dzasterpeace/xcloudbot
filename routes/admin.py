from flask import Blueprint, request, jsonify
from extensions import db
from models import User, TipsterAccess
from auth_helpers import superuser_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/tipsters', methods=['GET'])
@superuser_required
def list_all_tipsters(current_user):
    """
    ---
    tags:
      - Admin
    responses:
      200:
        description: List of all tipsters
    """
    tipsters = User.query.filter_by(role='tipster').all()
    return jsonify([{"id": t.id, "email": t.email} for t in tipsters])

@admin_bp.route('/admin/tipster/<int:tipster_id>/subscribers', methods=['GET'])
@superuser_required
def get_tipster_subscribers(current_user, tipster_id):
    """
    ---
    tags:
      - Admin
    parameters:
      - name: tipster_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of subscribers for the given tipster
    """
    access = TipsterAccess.query.filter_by(tipster_id=tipster_id).all()
    return jsonify([{"user_id": a.user_id, "email": a.user.email} for a in access])

@admin_bp.route('/admin/tipster/<int:tipster_id>/subscribers', methods=['POST'])
@superuser_required
def update_tipster_subscribers(current_user, tipster_id):
    """
    ---
    tags:
      - Admin
    parameters:
      - name: tipster_id
        in: path
        type: integer
        required: true
      - name: user_ids
        in: body
        type: array
        required: true
    responses:
      200:
        description: Updated tipster subscriber list
    """
    data = request.get_json()
    new_user_ids = set(data.get('user_ids', []))

    TipsterAccess.query.filter_by(tipster_id=tipster_id).delete()
    db.session.commit()

    for uid in new_user_ids:
        db.session.add(TipsterAccess(tipster_id=tipster_id, user_id=uid))
    db.session.commit()

    return jsonify({"message": f"{len(new_user_ids)} users now have access"})