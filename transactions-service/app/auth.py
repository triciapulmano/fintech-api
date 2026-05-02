from jose import jwt, JWTError
import os
from typing import Optional

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
USERS_SERVICE_URL = os.getenv("USERS_SERVICE_URL", "http://users-service:8001")
WALLET_SERVICE_URL = os.getenv("WALLET_SERVICE_URL", "http://wallet-service:8002")

def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token locally"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_token_from_header(authorization_header: str) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    if not authorization_header:
        return None
    
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    return parts[1]