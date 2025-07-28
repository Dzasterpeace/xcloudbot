from flask import Blueprint
from extensions import db
from models import  UserBet, TipsterTip, User
from betfair import BetfairBetPlacer, BetfairMarketLookup
from betfair.oauth_session import OAuthSessionManager
from datetime import datetime

cron_bp = Blueprint('cron', __name__)

@cron_bp.route('/cron/place_pending_bets', methods=['POST'])
def place_pending_bets():
    """
    ---
    tags:
      - Automate
    responses:
      200:
        description: Summary of bet placement attempt
    """
    now = datetime.utcnow()
    placed_count = 0
    failed_count = 0

    pending_bets = UserBet.query.filter_by(status='pending').all()

    for bet in pending_bets:
        tip = TipsterTip.query.get(bet.tip_id)
        user = User.query.get(bet.user_id)

        if not tip or not user:
            failed_count += 1
            continue

        if tip.race_time < now:
            bet.status = 'expired'
            db.session.commit()
            continue

        lookup = BetfairMarketLookup().find_market_and_selection_ids(
            course=tip.course,
            race_time=tip.race_time,
            horse=tip.horse
        )

        if not lookup:
            failed_count += 1
            continue

        placer = BetfairBetPlacer(user)
        result = placer.place_bet(
            market_id=lookup['market_id'],
            selection_id=lookup['selection_id'],
            side="BACK",
            stake=bet.stake,
            price=1.01
        )

        if result.get("success"):
            bet.status = "placed"
            db.session.commit()
            placed_count += 1
        else:
            failed_count += 1

    return {
        "message": f"{placed_count} bets placed, {failed_count} failed or skipped."
    }

@cron_bp.route('/cron/refresh_tokens', methods=['POST'])
def refresh_all_tokens():
    """
    ---
    tags:
      - Automate
    responses:
      200:
        description: Summary of token refresh results
    """
    users = User.query.all()
    refreshed = 0
    skipped = 0
    failed = 0

    for user in users:
        if not user.betfair_refresh_token:
            skipped += 1
            continue

        session_mgr = OAuthSessionManager(user)
        new_token = session_mgr.refresh_access_token()

        if new_token:
            refreshed += 1
        else:
            failed += 1

    return {
        "message": f"{refreshed} tokens refreshed, {skipped} skipped (no refresh token), {failed} failed"
    }
