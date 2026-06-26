import hmac
import hashlib
import base64
import json
import time
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.core.config import DATABASE_URL, SECRET_KEY
from backend.core.database import get_db
from backend.core.models import User as DBUser

ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def hash_password(password: str) -> str:
    """PBKDF2 SHA-256 secure password hashing utilizing standard library."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt.hex() + ":" + key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored PBKDF2 salt/key combination."""
    try:
        salt_hex, key_hex = hashed_password.split(":")
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        new_key = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False

def create_access_token(data: dict, expires_in: int = 3600) -> str:
    """Generates a standard HS256-signed JWT token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in
    
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"

def verify_access_token(token: str) -> dict:
    """Verifies access token signature and parses payload dictionary."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Validate signature
        expected_signature = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_signature).decode().rstrip("=")
        
        if sig_b64 != expected_sig_b64:
            return None
            
        # Decode payload
        padding = "=" * (4 - len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(payload_b64 + padding).decode()
        payload = json.loads(payload_json)
        
        # Verify expiration
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """FastAPI Dependency: Returns current logged-in DB user or anonymous placeholder."""
    # If no token is provided, default to an anonymous viewer for public endpoints
    if not token:
        # Check if anonymous user exists or return a temporary viewer mock
        anon = DBUser(username="anonymous", email="anonymous@iks.org", hashed_password="")
        anon.role = "Viewer"  # Dynamically set role for anonymous access
        return anon

    payload = verify_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    user = db.query(DBUser).filter(DBUser.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Ensure role is set on the user object (fallback to Viewer)
    if not hasattr(user, "role") or not user.role:
        user.role = "Viewer"
        
    return user

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: DBUser = Depends(get_current_user)):
        user_role = getattr(current_user, "role", "Viewer") or "Viewer"
        
        # Admin has super-user override permissions
        if user_role == "Admin":
            return current_user
            
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User role '{user_role}' is not authorized to access this resource. Allowed: {self.allowed_roles}"
            )
        return current_user

# Common Role Access Dependencies
require_viewer = RoleChecker(["Viewer", "Researcher", "Admin"])
require_researcher = RoleChecker(["Researcher", "Admin"])
require_admin = RoleChecker(["Admin"])
