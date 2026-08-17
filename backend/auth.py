"""
Authentication and security module using JWT tokens and bcrypt password hashing.
Supports HttpOnly secure cookies for web browsers and Bearer authorization for API clients.
"""
import os
import uuid
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .database import fetch_one, execute_query

# Configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "auraprice-super-secure-production-secret-key-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 Hours
COOKIE_NAME = "auraprice_session"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

optional_bearer = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    auth_creds: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer)
) -> Dict[str, Any]:
    """
    FastAPI dependency to extract and authenticate the current user.
    Checks HttpOnly cookie first, then Bearer token in Authorization header.
    """
    token = None
    # 1. Check HttpOnly Cookie
    if COOKIE_NAME in request.cookies:
        token = request.cookies[COOKIE_NAME]
    # 2. Check Authorization Bearer Header
    elif auth_creds and auth_creds.credentials:
        token = auth_creds.credentials
    # 3. Fallback check raw Authorization header
    elif "authorization" in request.headers:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if payload is None or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]
    user = fetch_one("SELECT user_id, email, display_name, created_at FROM users WHERE user_id = ?", (user_id,))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def register_user(email: str, password: str, display_name: str) -> Dict[str, Any]:
    """Registers a new user and creates default user settings."""
    email_clean = email.strip().lower()
    existing = fetch_one("SELECT user_id FROM users WHERE email = ?", (email_clean,))
    if existing:
        raise ValueError("An account with this email address already exists.")

    user_id = str(uuid.uuid4())
    hashed_pwd = get_password_hash(password)
    display = display_name.strip() or email_clean.split("@")[0]

    execute_query(
        "INSERT INTO users (user_id, email, password_hash, display_name) VALUES (?, ?, ?, ?)",
        (user_id, email_clean, hashed_pwd, display)
    )

    # Initialize default settings for user
    execute_query(
        """
        INSERT INTO user_settings (
            user_id, margin_floor_pct, corridor_min_pct, corridor_max_pct,
            max_discount_pct, max_price_change_pct, never_below_cost, never_above_mrp
        ) VALUES (?, 5.5, -25.0, 25.0, 40.0, 15.0, 1, 1)
        """,
        (user_id,)
    )

    return {
        "user_id": user_id,
        "email": email_clean,
        "display_name": display
    }

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticates email and password, returns user dict if valid."""
    email_clean = email.strip().lower()
    user = fetch_one("SELECT user_id, email, password_hash, display_name FROM users WHERE email = ?", (email_clean,))
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "display_name": user["display_name"]
    }
