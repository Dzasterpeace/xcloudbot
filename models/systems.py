from datetime import datetime
from extensions import db

class System(db.Model):
    __tablename__ = 'system'  # 👈 THIS LINE IS REQUIRED

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    system_type = db.Column(db.String(10), nullable=False)  # 'lay' or 'back'
    staking_plan = db.Column(db.String(50), nullable=False)
    bank = db.Column(db.Float, nullable=False)
