from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.base import Base
from datetime import datetime

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    host = Column(String(128), nullable=False, unique=True)
    username = Column(String(64), nullable=False)
    password = Column(String(256), nullable=False)  # Should be encrypted
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    last_used = Column(DateTime)
    status = Column(String(20), default='unknown')  # 'active', 'inactive', 'error'
    
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