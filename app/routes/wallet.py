from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Wallet
from app.auth import get_current_user

router = APIRouter()

@router.get("/")
def get_balance(current_user: User = Depends(get_current_user)):
    return {"balance": current_user.wallet.balance}


@router.post("/add-funds")
def add_funds(amount: float,
              current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):

    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not current_user.wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    print("Before:", current_user.wallet.balance)
    current_user.wallet.balance += amount
    print("After:", current_user.wallet.balance)
    db.commit()

    return {
        "message": "Funds added", 
        "new_balance": current_user.wallet.balance
    }