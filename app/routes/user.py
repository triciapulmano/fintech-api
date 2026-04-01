from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, Wallet
from app.schemas import UserCreate
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    print(f"Password: {user.password}, Length:{len(user.password)}")
    
    hashed_pw = pwd_context.hash(str(user.password)[:72])

    new_user = User(username=user.username, password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # create wallet automatically
    wallet = Wallet(user_id=new_user.id)
    db.add(wallet)
    db.commit()

    return {"message": "User created"}