from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, func
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import json

class CommandTemplate(Base):
    __tablename__ = "command_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    command = Column(Text, nullable=False)
    category = Column(String(50))  # e.g., 'virtual', 'pool', 'node'
    variables = Column(Text)  # JSON string of variable definitions
    created_by = Column(Integer, ForeignKey('users.id'))
    is_favorite = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)  # True for built-in commands
    
    # Relationships
    creator = relationship("User", backref="command_templates")
    
    def get_variables(self):
        if self.variables:
            return json.loads(self.variables)
        return {}

class CommandHistory(Base):
    __tablename__ = "command_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    device_id = Column(Integer, ForeignKey('devices.id'))
    command = Column(Text, nullable=False)
    output = Column(Text)
    status = Column(String(20))  # 'success', 'error', 'timeout'
    executed_at = Column(DateTime, default=func.now())
    execution_time = Column(Float)  # in seconds
    is_favorite = Column(Boolean, default=False)
    error_message = Column(Text)

    # Relationships
    user = relationship("User", backref="command_history")
    device = relationship("Device", backref="command_history")

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