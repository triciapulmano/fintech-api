from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., max_length=72)

class UserLogin(BaseModel):
    username: str
    password: str

class TransferRequest(BaseModel):
    receiver_username: str
    amount: float