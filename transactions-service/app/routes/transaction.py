from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
import logging
import httpx

from app.database import get_db
from app.models import Transaction, TransactionStatus
from app.schemas import SendTransactionRequest, TransactionResponse, TransactionHistoryResponse
from app.auth import decode_token, USERS_SERVICE_URL, WALLET_SERVICE_URL

router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

async def verify_token_with_users_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Zero-trust validation: Call users service to verify token
    """
    authorization = f"Bearer {credentials.credentials}"

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{USERS_SERVICE_URL}/users/verify-token",
                headers={"Authorization": authorization}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            
            user_data = response.json()
            return UUID(user_data["id"])
    
    except httpx.RequestError:
        logger.warning("Users service unavailable, using local token validation")
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        payload = decode_token(parts[1])
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return UUID(payload["sub"])

@router.post("/send", response_model=TransactionResponse, tags=["Transactions"])
async def send_transaction(
    request: SendTransactionRequest,
    user_id: UUID = Depends(verify_token_with_users_service),
    db: Session = Depends(get_db)
):
    """Send money to another user"""
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
     # Step 1: Lookup recipient by phone number
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{USERS_SERVICE_URL}/users/lookup/{request.to_phone_number}"
        )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Recipient not found")
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Could not resolve recipient")
        recipient_id = UUID(response.json()["id"])

    if recipient_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot send money to yourself")

    # Step 2: Create transaction as PENDING
    transaction = Transaction(
        from_user_id=user_id,
        to_user_id=recipient_id,
        amount=request.amount,
        status=TransactionStatus.PENDING,
        description=request.description
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    async with httpx.AsyncClient() as client:
        # Step 3: Deduct from sender
        deduct_response = await client.post(
            f"{WALLET_SERVICE_URL}/wallet/deduct",
            json={"user_id": str(user_id), "amount": request.amount}
        )

        if deduct_response.status_code == 400:
            # Insufficient funds - mark transaction as FAILED
            transaction.status = TransactionStatus.FAILED
            db.commit()
            raise HTTPException(status_code=400, detail="Insufficient funds")

        if deduct_response.status_code != 200:
            transaction.status = TransactionStatus.FAILED
            db.commit()
            raise HTTPException(status_code=502, detail="Failed to deduct funds")

        # Step 4: Credit recipient
        credit_response = await client.post(
            f"{WALLET_SERVICE_URL}/wallet/credit",
            json={"user_id": str(recipient_id), "amount": request.amount}
        )

        if credit_response.status_code != 200:
            # Credit failed - rollback sender deduction
            await client.post(
                f"{WALLET_SERVICE_URL}/wallet/credit",
                json={"user_id": str(user_id), "amount": request.amount}
            )
            transaction.status = TransactionStatus.FAILED
            db.commit()
            raise HTTPException(status_code=502, detail="Failed to credit recipient, transaction rolled back")

    # Step 5: Mark transaction as COMPLETED
    transaction.status = TransactionStatus.COMPLETED
    db.commit()
    db.refresh(transaction)
    
    logger.info(f"Transaction created: {user_id} -> {recipient_id}, Amount: {request.amount}")
    
    return TransactionResponse.model_validate(transaction)

@router.get("/history", response_model=TransactionHistoryResponse, tags=["Transactions"])
async def get_transaction_history(
    user_id: UUID = Depends(verify_token_with_users_service),
    db: Session = Depends(get_db)
):
    """Get transaction history for current user"""
    
    # Get sent transactions
    sent_transactions = db.query(Transaction).filter(
        Transaction.from_user_id == user_id
    ).order_by(Transaction.created_at.desc()).all()
    
    # Get received transactions
    received_transactions = db.query(Transaction).filter(
        Transaction.to_user_id == user_id
    ).order_by(Transaction.created_at.desc()).all()
    
    return TransactionHistoryResponse(
        sent=[TransactionResponse.model_validate(t) for t in sent_transactions],
        received=[TransactionResponse.model_validate(t) for t in received_transactions]
    )

@router.get("/{transaction_id}", response_model=TransactionResponse, tags=["Transactions"])
async def get_transaction(
    transaction_id: UUID,
    user_id: UUID = Depends(verify_token_with_users_service),
    db: Session = Depends(get_db)
):
    """Get transaction details"""
    
    transaction = db.query(Transaction).filter(
        (Transaction.id == transaction_id) &
        ((Transaction.from_user_id == user_id) | (Transaction.to_user_id == user_id))
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse.model_validate(transaction)