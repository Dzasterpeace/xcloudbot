from flask import Blueprint, request, jsonify
from auth_helpers import token_required
from extensions import db
from models import TipsterTip, System, User, SystemFollower, UserBet, TipsterAccess
from datetime import datetime

tips_bp = Blueprint('tips', __name__)

@tips_bp.route('/tips/upload', methods=['POST'])
@token_required
def upload_tips(current_user):
    """
    ---
    tags:
      - Tips
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - system_id
            - tips
          properties:
            system_id:
              type: integer
            tips:
              type: array
              items:
                type: object
                properties:
                  race_time:
                    type: string
                  course:
                    type: string
                  horse:
                    type: string
                  stake_type:
                    type: string
    responses:
      200:
        description: Tips uploaded and user bets created
      400:
        description: Missing system_id or tips
      403:
        description: Unauthorized
      404:
        description: System not found
    """
    data = request.get_json()

    system_id = data.get("system_id")
    tips = data.get("tips", [])

    if not system_id or not tips:
        return jsonify({"error": "Missing system_id or tips"}), 400

    system = System.query.get(system_id)
    if not system:
        return jsonify({"error": "System not found"}), 404

    if system.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    followers = SystemFollower.query.filter_by(system_id=system_id).all()
    created_tips = 0
    created_user_bets = 0

    for tip in tips:
        new_tip = TipsterTip(
            system_id=system_id,
            race_time=tip["race_time"],
            course=tip["course"],
            horse=tip["horse"],
            stake_type=tip.get("stake_type", "real"),
        )
        db.session.add(new_tip)
        db.session.flush()  # get new_tip.id

        for follower in followers:
            user_bet = UserBet(
                user_id=follower.user_id,
                tip_id=new_tip.id,
                stake=follower.stake,
                status="pending"
            )
            db.session.add(user_bet)
            created_user_bets += 1

        created_tips += 1

    db.session.commit()
    return jsonify({
        "message": f"{created_tips} tips uploaded and {created_user_bets} user bets created."
    })


@tips_bp.route('/tips/sync', methods=['POST'])
@token_required
def sync_tips(current_user):
    """
    ---
    tags:
      - Tips
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - system_id
          properties:
            system_id:
              type: integer
    responses:
      200:
        description: User bets synced to tips
      400:
        description: Missing system_id
      403:
        description: Unauthorized
      404:
        description: System not found
    """
    data = request.get_json()
    system_id = data.get("system_id")

    if not system_id:
        return jsonify({"error": "Missing system_id"}), 400

    system = System.query.get(system_id)
    if not system:
        return jsonify({"error": "System not found"}), 404

    is_owner = (system.user_id == current_user.id)
    is_authorized = TipsterAccess.query.filter_by(
        tipster_id=system.user_id,
        user_id=current_user.id
    ).first()

    if not is_owner and not is_authorized:
        return jsonify({"error": "Unauthorized"}), 403

    tips = TipsterTip.query.filter_by(system_id=system_id).all()
    followers = SystemFollower.query.filter_by(system_id=system_id).all()

    if not tips or not followers:
        return jsonify({"message": "No tips or followers found"}), 200

    created_bets = 0
    for follower in followers:
        for tip in tips:
            existing = UserBet.query.filter_by(user_id=follower.user_id, tip_id=tip.id).first()
            if existing:
                continue
            user_bet = UserBet(
                user_id=follower.user_id,
                tip_id=tip.id,
                stake=follower.stake,
                status="pending"
            )
            db.session.add(user_bet)
            created_bets += 1

    db.session.commit()
    return jsonify({"message": f"{created_bets} user bets created."})


@tips_bp.route('/tips/download', methods=['GET'])
@token_required
def download_tips(current_user):
    """
    ---
    tags:
      - Tips
    responses:
      200:
        description: Downloadable tips with authorized access
    """
    today = datetime.utcnow().date()

    followed = SystemFollower.query.filter_by(user_id=current_user.id).all()
    if not followed:
        return jsonify([])

    system_ids = [f.system_id for f in followed]
    stake_map = {f.system_id: f.stake for f in followed}

    tips = (
        db.session.query(TipsterTip, System)
        .join(System, TipsterTip.system_id == System.id)
        .filter(
            TipsterTip.system_id.in_(system_ids),
            db.func.date(TipsterTip.created_at) == today
        )
        .all()
    )

    downloadable = []
    for tip, system in tips:
        authorized = TipsterAccess.query.filter_by(
            tipster_id=system.user_id,
            user_id=current_user.id
        ).first()

        if authorized:
            downloadable.append({
                "system_id": system.id,
                "tip_id": tip.id,
                "race_time": tip.race_time,
                "course": tip.course,
                "horse": tip.horse,
                "stake_type": tip.stake_type,
                "stake": stake_map.get(system.id, 1.0),
            })

    return jsonify(downloadable)
