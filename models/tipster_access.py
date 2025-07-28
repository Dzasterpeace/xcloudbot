# models/tipster_access.py
from extensions import db

class TipsterAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipster_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    tipster = db.relationship('User', foreign_keys=[tipster_id])
    user = db.relationship('User', foreign_keys=[user_id])
