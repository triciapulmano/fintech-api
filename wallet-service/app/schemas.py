from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class AddFundsRequest(BaseModel):
    amount: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "amount": 100.50
            }
        }

class WalletResponse(BaseModel):
    id: UUID
    user_id: UUID
    balance: float
    currency: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DeductFundsRequest(BaseModel):
    user_id: UUID
    amount: float

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 50.00
            }
        }

class CreditFundsRequest(BaseModel):
    user_id: UUID
    amount: float

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "amount": 50.00
            }
        }