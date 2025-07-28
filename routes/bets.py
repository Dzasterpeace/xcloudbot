from flask import Blueprint, request, jsonify
from extensions import db
from models import Bet, UserBet, TipsterTip
from auth_helpers import token_required
from datetime import datetime

bets_bp = Blueprint('bets', __name__)

@bets_bp.route('/bets/create', methods=['POST'])
@token_required
def create_bet(current_user):
    """
    ---
    tags:
      - Bets
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - system_id
            - time
            - course
            - horse
            - stake
          properties:
            system_id:
              type: integer
            time:
              type: string
            course:
              type: string
            horse:
              type: string
            type:
              type: string
            stake:
              type: number
            odds:
              type: number
    responses:
      201:
        description: Bet created
      400:
        description: Missing fields
    """
    data = request.get_json()
    required_fields = ['system_id', 'time', 'course', 'horse', 'stake']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    bet = Bet(
        user_id=current_user.id,
        system_id=data['system_id'],
        time=data['time'],
        course=data['course'],
        horse=data['horse'],
        type=data.get('type', '1pt win'),
        stake=data['stake'],
        odds=data.get('odds')
    )
    db.session.add(bet)
    db.session.commit()
    return jsonify({"message": "Bet created", "bet": bet.to_dict()}), 201

@bets_bp.route('/bets', methods=['GET'])
@token_required
def list_bets(current_user):
    """
    ---
    tags:
      - Bets
    parameters:
      - name: system_id
        in: query
        type: string
        required: true
    responses:
      200:
        description: List of bets
    """
    system_id = request.args.get('system_id')
    if not system_id:
        return jsonify({"error": "system_id required"}), 400

    bets = Bet.query.filter_by(system_id=system_id, user_id=current_user.id).order_by(Bet.created_at.desc()).all()
    return jsonify([b.to_dict() for b in bets])

@bets_bp.route('/bets/<int:bet_id>/delete', methods=['DELETE'])
@token_required
def delete_bet(current_user, bet_id):
    """
    ---
    tags:
      - Bets
    parameters:
      - name: bet_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Bet deleted
      404:
        description: Bet not found
    """
    bet = Bet.query.filter_by(id=bet_id, user_id=current_user.id).first()
    if not bet:
        return jsonify({"error": "Bet not found"}), 404
    db.session.delete(bet)
    db.session.commit()
    return jsonify({"message": "Bet deleted"})

@bets_bp.route('/bets/pending', methods=['GET'])
@token_required
def get_pending_bets(current_user):
    """
    ---
    tags:
      - Bets
    responses:
      200:
        description: List of pending bets grouped by race
    """
    user_bets = (
        db.session.query(UserBet)
        .join(TipsterTip)
        .filter(UserBet.user_id == current_user.id, UserBet.status == 'pending')
        .order_by(TipsterTip.race_time.asc())
        .all()
    )

    bets_by_race = {}

    for bet in user_bets:
        tip = bet.tip
        key = f"{tip.race_time} | {tip.course}"

        if key not in bets_by_race:
            bets_by_race[key] = {
                "date": tip.race_time.split()[0] if " " in tip.race_time else "Unknown",
                "time": tip.race_time,
                "course": tip.course,
                "selections": []
            }

        bets_by_race[key]["selections"].append({
            "horse": tip.horse,
            "stake": bet.stake,
            "status": bet.status
        })

    return jsonify(list(bets_by_race.values()))
