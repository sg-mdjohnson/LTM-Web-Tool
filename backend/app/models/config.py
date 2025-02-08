from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base
import json

class UserConfig(Base):
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # Theme preferences
    theme = Column(String(50), default='dark')
    theme_customization = Column(Text)  # JSON string
    
    # CLI preferences
    cli_preferences = Column(Text)  # JSON string
    
    # Timeout settings
    timeout_settings = Column(Text)  # JSON string
    
    # Relationship
    user = relationship("User", back_populates="config")
    
    def get_theme_customization(self):
        if self.theme_customization:
            return json.loads(self.theme_customization)
        return {}
    
    def get_cli_preferences(self):
        if self.cli_preferences:
            return json.loads(self.cli_preferences)
        return {}
    
    def get_timeout_settings(self):
        if self.timeout_settings:
            return json.loads(self.timeout_settings)
        return {
            'api': 30,
            'ssh': 60
        } 