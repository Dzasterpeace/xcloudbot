import requests
import logging
from betfair.oauth_session import OAuthSessionManager
import os

class BetfairBetPlacer:
    PLACE_ORDERS_URL = "https://api.betfair.com/exchange/betting/rest/v1.0/placeOrders/"

    def __init__(self, user, commit_func=None):
        self.user = user
        # OAuthSessionManager will handle refreshing and persisting tokens
        self.session_manager = OAuthSessionManager(user, commit_func=commit_func)
    
    def place_bet(self, market_id, selection_id, side, stake, price):
        # Ensure we have a valid access token (refresh if needed)
        token = self.session_manager.get_access_token()
        if not token:
            return {"error": "Failed to obtain Betfair access token"}

        headers = {
            'X-Application': os.getenv("BETFAIR_CLIENT_ID"),
            'X-Authentication': token,
            'Content-Type': 'application/json'
        }

        payload = {
            "marketId": market_id,
            "instructions": [
                {
                    "selectionId": selection_id,
                    "handicap": 0,
                    "side": side.upper(),  # BACK or LAY
                    "orderType": "LIMIT",
                    "limitOrder": {
                        "size": stake,
                        "price": price,
                        "persistenceType": "LAPSE"
                    }
                }
            ],
            "customerRef": f"XCloud-{self.user.id}"
        }

        try:
            resp = requests.post(self.PLACE_ORDERS_URL, headers=headers, json=payload)
            data = resp.json()

            if data.get("status") == "SUCCESS":
                return {"success": True, "details": data}

            logging.warning("Bet placement failed for user %s: %s", self.user.id, data)
            return {"error": data}

        except Exception as e:
            logging.exception("Error placing bet via OAuth for user %s", self.user.id)
            return {"error": str(e)}
