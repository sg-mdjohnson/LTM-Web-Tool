from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
import enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
from app.core.security import verify_password, get_password_hash

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)

    # Relationships
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    configs = relationship("UserConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.hashed_password = get_password_hash(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.hashed_password)

    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def has_permission(self, permission: str) -> bool:
        if self.is_admin():
            return True
        # Add permission checking logic based on role
        return False 