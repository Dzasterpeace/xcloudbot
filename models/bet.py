from extensions import db

class Bet(db.Model):
    __tablename__ = 'bet'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stake   = db.Column(db.Float, nullable=False)
    odds    = db.Column(db.Float, nullable=False)
    result  = db.Column(db.String(10))  # 'won', 'lost', etc.

    # avoid colliding with UserBet.bets backref
    user = db.relationship(
        'User',
        backref=db.backref('simple_bets', lazy=True)
    )
