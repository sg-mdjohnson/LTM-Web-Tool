from app import db
from datetime import datetime
import json

class CommandTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    command = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # e.g., 'virtual', 'pool', 'node'
    variables = db.Column(db.Text)  # JSON string of variable definitions
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_favorite = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)  # True for built-in commands
    
    def get_variables(self):
        if self.variables:
            return json.loads(self.variables)
        return {}

class CommandHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    command = db.Column(db.Text, nullable=False)
    output = db.Column(db.Text)
    status = db.Column(db.String(20))  # 'success', 'error', 'timeout'
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    execution_time = db.Column(db.Float)  # in seconds
    is_favorite = db.Column(db.Boolean, default=False)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'command': self.command,
            'output': self.output,
            'status': self.status,
            'executed_at': self.executed_at.isoformat(),
            'execution_time': self.execution_time,
            'is_favorite': self.is_favorite,
            'error_message': self.error_message
        } 