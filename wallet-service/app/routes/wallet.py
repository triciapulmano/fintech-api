from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from uuid import UUID
import httpx
import logging

from app.database import get_db
from app.models import Wallet
from app.schemas import AddFundsRequest, DeductFundsRequest, WalletResponse, CreditFundsRequest
from app.auth import decode_token, USERS_SERVICE_URL


router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

async def verify_token_with_users_service(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Zero-trust validation: Call users service to verify token
    Every request validates the token with users service
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
        # Fallback: decode locally if users service unavailable (circuit breaker pattern)
        logger.warning("Users service unavailable, using local token validation")
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        payload = decode_token(parts[1])
        if not payload or "sub" not in payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        return UUID(payload["sub"])

@router.get("", response_model=WalletResponse, tags=["Wallet"])
async def get_wallet(
    user_id: UUID = Depends(verify_token_with_users_service),
    db: Session = Depends(get_db)
):
    """Get user's wallet"""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    if not wallet:
        # Create wallet if doesn't exist
        wallet = Wallet(user_id=user_id, balance=0.0)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    
    return WalletResponse.model_validate(wallet)

@router.post("/add-funds", response_model=WalletResponse, tags=["Wallet"])
async def add_funds(
    request: AddFundsRequest,
    user_id: UUID = Depends(verify_token_with_users_service),
    db: Session = Depends(get_db)
):
    """Add funds to wallet (for testing)"""
    
    if request.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    
    if not wallet:
        wallet = Wallet(user_id=user_id, balance=request.amount)
    else:
        wallet.balance += request.amount
    
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    
    logger.info(f"Added {request.amount} to wallet for user {user_id}")
    
    return WalletResponse.model_validate(wallet)

@router.post("/deduct", response_model=WalletResponse, tags=["Internal"])
async def deduct_funds(
    request: DeductFundsRequest,
    db: Session = Depends(get_db)
):
    """Internal endpoint - deduct funds from a user's wallet"""
    wallet = db.query(Wallet).filter(Wallet.user_id == request.user_id).first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    if wallet.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")
    
    wallet.balance -= request.amount
    db.commit()
    db.refresh(wallet)
    
    logger.info(f"Deducted {request.amount} from user {request.user_id}, new balance: {wallet.balance}")
    
    return WalletResponse.model_validate(wallet)

@router.post("/credit", response_model=WalletResponse, tags=["Internal"])
async def credit_funds(
    request: CreditFundsRequest,
    db: Session = Depends(get_db)
):
    """Internal endpoint - credit funds to a user's wallet"""
    wallet = db.query(Wallet).filter(Wallet.user_id == request.user_id).first()
    
    if not wallet:
        # Auto-create wallet if doesn't exist
        wallet = Wallet(user_id=request.user_id, balance=request.amount)
    else:
        wallet.balance += request.amount
    
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    
    logger.info(f"Credited {request.amount} to user {request.user_id}, new balance: {wallet.balance}")
    
    return WalletResponse.model_validate(wallet)