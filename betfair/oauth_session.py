import requests
import logging
import os
from datetime import datetime, timedelta

class OAuthSessionManager:
    """
    Manages Betfair OAuth2 sessions: retrieves and refreshes access tokens using stored refresh tokens.
    """
    TOKEN_URL = "https://identitysso.betfair.com/api/oauth2/token"

    def __init__(self, user, commit_func=None):
        self.user = user
        # Load client credentials from environment
        self.client_id = os.getenv("BETFAIR_CLIENT_ID")
        self.client_secret = os.getenv("BETFAIR_CLIENT_SECRET")
        # Optional callback for committing user updates (e.g., db.session.commit)
        self.commit = commit_func or (lambda: None)

    def get_access_token(self):
        """
        Returns a valid access token, refreshing it if expired or not present.
        """
        expiry = self.user.betfair_token_expiry
        if expiry and expiry > datetime.utcnow() + timedelta(seconds=60):
            return self.user.betfair_access_token
        return self.refresh_access_token()

    def refresh_access_token(self):
        """
        Uses the stored refresh token to obtain a new access token from Betfair.
        Updates the user record with new tokens and expiry.
        """
        refresh_token = self.user.betfair_refresh_token
        if not refresh_token:
            logging.error("No refresh token available for user %s", self.user.id)
            return None

        payload = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        auth = (self.client_id, self.client_secret)

        try:
            response = requests.post(
                self.TOKEN_URL,
                data=payload,
                auth=auth,
                timeout=10
            )
            data = response.json()
            if 'access_token' in data:
                # Update user with new tokens
                self.user.betfair_access_token = data['access_token']
                # Some flows may return a new refresh token
                if 'refresh_token' in data:
                    self.user.betfair_refresh_token = data['refresh_token']
                # Set new expiry
                expires_in = int(data.get('expires_in', 0))
                self.user.betfair_token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                # Persist changes
                try:
                    self.commit()
                except Exception:
                    logging.exception("Failed to commit refreshed tokens for user %s", self.user.id)
                return self.user.betfair_access_token

            logging.error("Failed to refresh token: %s", data)
            return None

        except Exception as e:
            logging.exception("Error refreshing Betfair access token for user %s", self.user.id)
            return None
