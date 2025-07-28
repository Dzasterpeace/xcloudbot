from datetime import datetime
from extensions import db
from cryptography.fernet import Fernet
import os

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed login pw
    role = db.Column(db.String(50), nullable=False, default='user')
    is_superuser = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    systems = db.relationship('System', backref='owner', lazy=True)

    # 🔐 OAuth2-based Betfair integration (encrypted tokens)
    _betfair_access_token = db.Column("betfair_access_token", db.String(1000))  # encrypted
    _betfair_refresh_token = db.Column("betfair_refresh_token", db.String(1000))  # encrypted
    betfair_token_expiry = db.Column(db.DateTime)  # token expiration datetime

    def _fernet(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            raise RuntimeError("ENCRYPTION_KEY not set in environment")
        return Fernet(key.encode())

    @property
    def betfair_access_token(self):
        """Decrypt and return the stored access token."""
        if not self._betfair_access_token:
            return None
        return self._fernet().decrypt(self._betfair_access_token.encode()).decode()

    @betfair_access_token.setter
    def betfair_access_token(self, token: str):
        """Encrypt and store a new access token."""
        self._betfair_access_token = self._fernet().encrypt(token.encode()).decode()

    @property
    def betfair_refresh_token(self):
        """Decrypt and return the stored refresh token."""
        if not self._betfair_refresh_token:
            return None
        return self._fernet().decrypt(self._betfair_refresh_token.encode()).decode()

    @betfair_refresh_token.setter
    def betfair_refresh_token(self, token: str):
        """Encrypt and store a new refresh token."""
        self._betfair_refresh_token = self._fernet().encrypt(token.encode()).decode()
