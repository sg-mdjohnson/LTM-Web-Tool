from typing import Optional
from pydantic import BaseModel, EmailStr, constr, validator
from datetime import datetime
from app.core.validators import validate_password

class UserBase(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    is_active: Optional[bool] = True

class UserCreate(UserBase):
    password: constr(min_length=8, max_length=100)

    @validator("password")
    def validate_password_strength(cls, v):
        is_valid, message = validate_password(v)
        if not is_valid:
            raise ValueError(message)
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    password: Optional[constr(min_length=8, max_length=100)] = None

    @validator("password")
    def validate_password_strength(cls, v):
        if v is not None:
            is_valid, message = validate_password(v)
            if not is_valid:
                raise ValueError(message)
        return v

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 