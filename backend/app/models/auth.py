from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True

class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class DeviceBase(BaseModel):
    name: str
    host: str
    username: str
    description: Optional[str] = None

class DeviceCreate(DeviceBase):
    password: str

class DeviceResponse(DeviceBase):
    id: int
    status: str = "inactive"
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True 