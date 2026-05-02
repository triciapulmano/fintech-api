from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List, Optional
from enum import Enum

class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class SendTransactionRequest(BaseModel):
    to_phone_number: str
    amount: float
    description: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "to_phone_number": "+1111111111",
                "amount": 50.00,
                "description": "Payment for services"
            }
        }

class TransactionResponse(BaseModel):
    id: UUID
    from_user_id: UUID
    to_user_id: UUID
    amount: float
    currency: str
    status: TransactionStatus
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TransactionHistoryResponse(BaseModel):
    sent: List[TransactionResponse]
    received: List[TransactionResponse]