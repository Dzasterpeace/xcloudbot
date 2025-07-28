import requests
import logging

class BetfairSessionManager:
    """
    Handles Betfair certificate-based login to obtain a session token.
    """
    LOGIN_URL = "https://identitysso-cert.betfair.com/api/certlogin"

    def __init__(self, user):
        self.username = user.betfair_username
        self.password = user.betfair_password      # 🔐 Decrypted via @property on User
        self.app_key = user.betfair_app_key
        self.cert_path = user.betfair_cert_path
        self.key_path = user.betfair_key_path
        self.session_token = None

    def login(self):
        headers = {
            'X-Application': self.app_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        payload = {
            'username': self.username,
            'password': self.password
        }

        try:
            response = requests.post(
                self.LOGIN_URL,
                data=payload,
                headers=headers,
                cert=(self.cert_path, self.key_path),
                timeout=10
            )
            data = response.json()
            if data.get("status") == "SUCCESS":
                self.session_token = data["sessionToken"]
                return self.session_token

            logging.error("Betfair login failed for user %s: %s", self.username, data)
            return None

        except Exception as e:
            logging.exception("Error during Betfair login for user %s", self.username)
            return None
