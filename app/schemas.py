from pydantic import BaseModel, Field

class UserCreate(BaseModel):
    username: str
    password: str = Field(..., max_length=72)