from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine
from app.models import User, UserConfig
from app.auth.jwt import get_password_hash

def init_db(db: Session) -> None:
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Check if we have users
    user = db.query(User).first()
    if not user:
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            password_hash=get_password_hash("admin"),
            role="admin",
            is_active=True
        )
        # Create default config for admin
        admin_config = UserConfig(user=admin)
        
        db.add(admin)
        db.add(admin_config)
        db.commit() 