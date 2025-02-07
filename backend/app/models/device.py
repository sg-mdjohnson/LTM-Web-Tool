from app import db
from datetime import datetime

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    host = db.Column(db.String(128), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Should be encrypted
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='unknown')  # 'active', 'inactive', 'error'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'host': self.host,
            'username': self.username,
            'description': self.description,
            'status': self.status,
            'last_used': self.last_used.isoformat() if self.last_used else None
        } 