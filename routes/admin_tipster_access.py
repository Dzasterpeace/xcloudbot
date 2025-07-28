from flask import Blueprint, request, jsonify
from auth_helpers import token_required
from extensions import db
from models import User, TipsterAccess

admin_tipster_access_bp = Blueprint('admin_tipster_access', __name__)

@admin_tipster_access_bp.route('/admin/tipster/<int:tipster_id>/access', methods=['GET'])
@token_required
def view_tipster_access(current_user, tipster_id):
    """
    ---
    tags:
      - Admin Tipster Access
    parameters:
      - name: tipster_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: List of users with access to this tipster
      403:
        description: Unauthorized
    """
    if not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403

    access = TipsterAccess.query.filter_by(tipster_id=tipster_id).all()
    users = [
        {
            "user_id": record.user.id,
            "email": record.user.email,
            "first_name": record.user.first_name,
            "last_name": record.user.last_name
        }
        for record in access
    ]
    return jsonify(users)


@admin_tipster_access_bp.route('/admin/tipster/<int:tipster_id>/access', methods=['POST'])
@token_required
def update_tipster_access(current_user, tipster_id):
    """
    ---
    tags:
      - Admin Tipster Access
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
        description: Access list updated
      403:
        description: Unauthorized
    """
    if not current_user.is_superuser:
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json()
    user_ids = set(data.get("user_ids", []))

    TipsterAccess.query.filter_by(tipster_id=tipster_id).delete()
    db.session.commit()

    for uid in user_ids:
        db.session.add(TipsterAccess(tipster_id=tipster_id, user_id=uid))

    db.session.commit()
    return jsonify({"message": f"{len(user_ids)} users granted access to tipster {tipster_id}"})