from extensions import db

class SystemFollower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey('system.id'), nullable=False)
    stake = db.Column(db.Float, nullable=False)
    bank = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref=db.backref('followed_systems', lazy=True))
    system = db.relationship('System', backref=db.backref('followers', lazy=True))
