# app/routes/transaction.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import User, Transaction
from app.auth import get_current_user

router = APIRouter(prefix="/transactions")

@router.post("/send")
def send_money(receiver_username: str, amount: float,
               current_username: str = Depends(get_current_user),
               db: Session = Depends(get_db)):

    sender = current_username
    receiver = db.query(User).filter(User.username == receiver_username).first()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    if not sender.wallet:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
    if not receiver.wallet:
        raise HTTPException(status_code=404, detail="Receiver wallet not found")
    if sender.wallet.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    # Update balances
    sender.wallet.balance -= amount
    receiver.wallet.balance += amount

    # Save transaction
    transaction = Transaction(
        sender_id=sender.id, 
        receiver_id=receiver.id, 
        amount=amount
        )
    
    db.add(transaction)
    db.commit()

    return {"message": "Transfer successful"}