from sqlalchemy.ext.declarative import declarative_base
from app.db.base_class import Base
from app.models.user import User
from app.models.device import Device
from app.models.config import UserConfig

Base = declarative_base() 