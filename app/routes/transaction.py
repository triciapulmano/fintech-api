from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import User, Transaction
from app.auth import get_current_user
from app.schemas import TransferRequest

router = APIRouter()

@router.post("/send")
def send_money(request: TransferRequest,
               current_username: User = Depends(get_current_user),
               db: Session = Depends(get_db)):

    sender = current_username
    receiver = db.query(User).filter(User.username == request.receiver_username).first()
    amount = request.amount

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")
    if not sender.wallet:
        raise HTTPException(status_code=404, detail="Sender wallet not found")
    if not receiver.wallet:
        raise HTTPException(status_code=404, detail="Receiver wallet not found")
    if sender.wallet.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    if sender.id == receiver.id:
        raise HTTPException(status_code=400, detail="Cannot send to yourself")

    # Update balances
    try:
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
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")

@router.get("/history")
def transaction_history(type: Optional[str] = None,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    
    transactions = db.query(Transaction).filter(
        (Transaction.sender_id == current_user.id) | 
        (Transaction.receiver_id == current_user.id)
    ).all()
    print(transactions)

    history = []

    for t in transactions:
        ts = t.timestamp.isoformat() if t.timestamp else None
        
        if type not in (None, "sent", "received"):
            raise HTTPException(status_code=400, detail="Invalid type")
        if t.sender_id == current_user.id:
            if type is None or type == "sent": 
                history.append({
                    "type": "sent",
                    "to": t.receiver.username if t.receiver else "Deleted user",
                    "amount": t.amount,
                    "timestamp": ts
                })
        else:
            if type is None or type == "received": 
                history.append({
                    "type": "received",
                    "from": t.sender.username if t.sender else "Deleted user",
                    "amount": t.amount,
                    "timestamp": ts
                })

    history.sort(key=lambda x: x["timestamp"], reverse=True)
    return {"history": history}