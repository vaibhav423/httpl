from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    hostname = db.Column(db.String(64))
    ip_address = db.Column(db.String(15))
    is_active = db.Column(db.Boolean, default=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_sites = db.relationship('BlockedSite', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.mac_address} ({self.ip_address})>'

    @property
    def connection_status(self):
        if not self.is_active:
            return 'Disconnected'
        if (datetime.utcnow() - self.last_seen).seconds > 300:  # 5 minutes threshold
            return 'Inactive'
        return 'Connected'

class BlockedSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<BlockedSite {self.domain} for user {self.user_id}>'
