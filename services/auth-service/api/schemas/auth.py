"""
Authentication Schemas
Pydantic models for request/response validation
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime


class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    first_name: Optional[str] = Field(None, max_length=50, description="First name")
    last_name: Optional[str] = Field(None, max_length=50, description="Last name")
    initial_capital: Optional[float] = Field(None, gt=0, description="Starting capital (USD)")

    @validator('password')
    def password_strength(cls, v):
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('username')
    def username_alphanumeric(cls, v):
        """Validate username is alphanumeric."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Username must be alphanumeric (underscores allowed)')
        return v


class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Password")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""
    refresh_token: str = Field(..., description="Valid refresh token")


class UserResponse(BaseModel):
    """User response (safe fields only)."""
    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_superuser: bool
    current_capital: Optional[float] = None
    initial_capital: Optional[float] = None
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True  # Pydantic v2
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "trader@example.com",
                "username": "trader1",
                "first_name": "John",
                "last_name": "Doe",
                "is_active": True,
                "is_verified": True,
                "is_superuser": False,
                "current_capital": 10000.0,
                "initial_capital": 10000.0,
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T12:00:00Z"
            }
        }


class LoginResponse(BaseModel):
    """Login response with tokens and user data."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")
    user: UserResponse

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "trader@example.com",
                    "username": "trader1",
                    "is_active": True
                }
            }
        }


class TokenResponse(BaseModel):
    """Token refresh response."""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800
            }
        }


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "message": "User registered successfully",
                "detail": "Please verify your email address"
            }
        }
