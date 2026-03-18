"""Authentication routes for user registration and login."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db
from ..models import User
from ..auth import create_access_token, create_refresh_token, ALGORITHM, SECRET_KEY
from jose import jwt

router = APIRouter(prefix="/api/auth", tags=["authentication"])


# Pydantic models
class UserRegister(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: int


class UserResponse(BaseModel):
    """User response."""
    id: int
    email: str
    is_active: bool

    class Config:
        from_attributes = True


def hash_password(password: str) -> str:
    """Hash a password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    """Register a new user."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        password_hash=password_hash,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate tokens with user_id in payload
    access_token = create_access_token(data={"sub": user_data.email, "user_id": user.id})
    refresh_token = create_refresh_token(data={"sub": user_data.email, "user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id
    )


@router.post("/login", response_model=TokenResponse)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    """Login user and return tokens."""
    # Find user
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled"
        )
    
    # Generate tokens with user_id in payload
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    refresh_token = create_refresh_token(data={"sub": user.email, "user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    refresh_token_str: str,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(refresh_token_str, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            user_id = int(payload.get("sub")) if payload.get("sub").isdigit() else None
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user"
        )
    
    # Generate new access token
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id})
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(get_db),
):
    """Get current user info."""
    # This endpoint is just for reference - would need the actual get_current_user dependency
    return UserResponse.from_orm(current_user)
