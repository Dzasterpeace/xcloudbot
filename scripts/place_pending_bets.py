import os
import logging
from datetime import datetime
from app import create_app
from extensions import db
from models import User, UserBet, TipsterTip
from betfair.bet_placer import BetfairBetPlacer
from betfair.lookup_market import get_market_and_selection_id

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

# Setup app context
app = create_app()
app.app_context().push()

def place_all_pending_bets():
    pending_bets = UserBet.query.filter_by(status='pending').all()
    logging.info(f"Found {len(pending_bets)} pending bets")

    for bet in pending_bets:
        user = User.query.get(bet.user_id)
        tip = TipsterTip.query.get(bet.tip_id)

        if not all([user, tip]):
            logging.warning(f"Missing user or tip for bet {bet.id}")
            continue

        if not all([user.betfair_username, user.betfair_app_key, user.betfair_cert_path, user.betfair_key_path]):
            logging.warning(f"User {user.id} missing Betfair credentials, skipping")
            continue

        placer = BetfairBetPlacer(user)

        # Lookup market & selection ID from tip
        market_id, selection_id = get_market_and_selection_id(tip.course, tip.race_time, tip.horse)

        if not market_id or not selection_id:
            logging.warning(f"Market/selection lookup failed for bet {bet.id}: {tip.horse} at {tip.course}")
            bet.status = 'failed'
            db.session.commit()
            continue

        # Place bet
        result = placer.place_bet(
            market_id=market_id,
            selection_id=selection_id,
            side='BACK',
            stake=bet.stake,
            price=5.0  # Optional: dynamically calculate or fetch best available
        )

        if result.get("success"):
            bet.status = 'placed'
            logging.info(f"Bet {bet.id} placed successfully")
        else:
            bet.status = 'failed'
            logging.warning(f"Bet {bet.id} failed: {result.get('error')}")

        db.session.commit()

if __name__ == '__main__':
    place_all_pending_bets()
