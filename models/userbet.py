from extensions import db
from datetime import datetime

class UserBet(db.Model):
    __tablename__ = 'user_bet'
    __table_args__ = {'extend_existing': True}

    id       = db.Column(db.Integer, primary_key=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tip_id   = db.Column(db.Integer, db.ForeignKey('tipster_tip.id'), nullable=False)
    stake    = db.Column(db.Float, nullable=False)
    status   = db.Column(db.String(20), default='pending')  # 'pending', 'placed', etc.

    # renamed backref so it doesn't clash with Bet.simple_bets
    user = db.relationship(
        'User',
        backref=db.backref('user_bets', lazy=True)
    )
    tip  = db.relationship(
        'TipsterTip',
        backref=db.backref('user_bets_records', lazy=True)
    )

    @staticmethod
    def get_pending_bets_for_user(user_id):
        from .tipstertip import TipsterTip
        from .systems   import System

        pending = (
            db.session.query(UserBet, TipsterTip, System)
            .join(TipsterTip, UserBet.tip_id == TipsterTip.id)
            .join(System, TipsterTip.system_id == System.id)
            .filter(UserBet.user_id == user_id, UserBet.status == 'pending')
            .all()
        )

        result = []
        for ub, tip, system in pending:
            result.append({
                "time":   tip.race_time.strftime("%H:%M"),
                "course": tip.course,
                "horse":  tip.horse,
                "stake":  ub.stake,
                "system": system.name
            })
        return result
