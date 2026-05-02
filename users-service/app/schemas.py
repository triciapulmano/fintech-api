from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserRegister(BaseModel):
    phone_number: str
    username: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+1234567890",
                "username": "john_doe",
                "password": "SecurePass123!"
            }
        }

class UserLogin(BaseModel):
    phone_number: str
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+1234567890",
                "password": "SecurePass123!"
            }
        }

class UserResponse(BaseModel):
    id: UUID
    username: str
    phone_number: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse