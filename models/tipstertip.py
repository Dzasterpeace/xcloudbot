from .systems import System
from extensions import db
from datetime import datetime

class TipsterTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    system_id = db.Column(db.Integer, db.ForeignKey('system.id'), nullable=False)
    race_time = db.Column(db.String(20))
    course = db.Column(db.String(100))
    horse = db.Column(db.String(100))
    stake_type = db.Column(db.String(20))  # 'real' or 'sim'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    system = db.relationship('System', backref=db.backref('tips', lazy=True))
