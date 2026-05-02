from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import User
from app.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from app.auth import hash_password, verify_password, create_access_token, decode_token

router = APIRouter()
logger = logging.getLogger(__name__)

security = HTTPBearer()

@router.post("/register", response_model=TokenResponse)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and return JWT token"""
    print("HIT USERS SERVICE REGISTER")
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.phone_number == user_data.phone_number) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    print("Password:", user_data.password)
    print("Type:", type(user_data.password))
    print("Length:", len(user_data.password))
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        phone_number=user_data.phone_number,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    token = create_access_token(
        data={"sub": str(new_user.id), "phone": new_user.phone_number}
    )
    
    logger.info(f"User registered: {new_user.username} ({new_user.phone_number})")
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(new_user)
    )

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and return JWT token"""
    print("LOGIN ENDPOINT HIT")
    # Find user by phone number
    user = db.query(User).filter(User.phone_number == credentials.phone_number).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate JWT token
    token = create_access_token(
        data={"sub": str(user.id), "phone": user.phone_number}
    )
    
    logger.info(f"User logged in: {user.username}")
    
    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )

@router.post("/verify-token", response_model=UserResponse)
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    Verify JWT token - used by other microservices
    Zero-trust validation: each service calls this endpoint
    """
    authorization = f"Bearer {credentials.credentials}" 
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    
    # Decode token
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Get user_id from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse.model_validate(user)

@router.get("/me", response_model=UserResponse)
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user info"""

    authorization = f"Bearer {credentials.credentials}" 
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return UserResponse.model_validate(user)

@router.get("/lookup/{phone_number}", response_model=UserResponse)
def lookup_user_by_phone(phone_number: str, db: Session = Depends(get_db)):
    """Lookup user by phone number - used internally by other services"""
    
    user = db.query(User).filter(User.phone_number == phone_number).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.model_validate(user)