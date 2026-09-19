"""Authentication routes for user login and registration."""

import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr

# Add shared to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.database.connection import get_db_session
from shared.database.models import User
from shared.utils.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from shared.utils.dependencies import get_current_user


logger = logging.getLogger(__name__)

router = APIRouter()


class TokenResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str
    expires_in: int  # seconds


class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    username: str
    password: str
    first_name: str | None = None
    last_name: str | None = None


class UserResponse(BaseModel):
    """User profile response."""
    id: str
    email: str
    username: str
    first_name: str | None
    last_name: str | None
    is_active: bool
    is_verified: bool
    created_at: str


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["auth"],
    summary="Register new user",
    description="Create a new user account"
)
async def register_user(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Register a new user."""
    try:
        # Check if email already exists
        result = await session.execute(
            select(User).where(User.email == request.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        result = await session.execute(
            select(User).where(User.username == request.username)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        hashed_password = get_password_hash(request.password)

        # Create new user
        new_user = User(
            email=request.email,
            username=request.username,
            hashed_password=hashed_password,
            first_name=request.first_name,
            last_name=request.last_name,
            is_active=True,
            is_verified=False,  # Email verification can be added later
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        logger.info(f"New user registered: {new_user.username} ({new_user.email})")

        return UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            username=new_user.username,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            is_active=new_user.is_active,
            is_verified=new_user.is_verified,
            created_at=new_user.created_at.isoformat() if new_user.created_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Login user",
    description="Authenticate user and return JWT access token"
)
async def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: AsyncSession = Depends(get_db_session),
):
    """
    Login user with username/email and password.

    Returns JWT access token for authenticated requests.
    """
    try:
        # Find user by username or email
        result = await session.execute(
            select(User).where(
                (User.username == form_data.username) | (User.email == form_data.username)
            )
        )
        user = result.scalar_one_or_none()

        # Verify credentials
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        logger.info(f"User logged in: {user.username}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login"
        )


@router.get(
    "/me",
    response_model=UserResponse,
    tags=["auth"],
    summary="Get current user",
    description="Get the profile of the currently authenticated user"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat() if current_user.created_at else None,
    )


@router.post(
    "/logout",
    tags=["auth"],
    summary="Logout user",
    description="Logout the current user (client should discard the token)"
)
async def logout_user(
    current_user: User = Depends(get_current_user),
):
    """
    Logout user.

    Note: JWTs are stateless, so logout is handled client-side by discarding the token.
    This endpoint is provided for API consistency and can be extended with token blacklisting.
    """
    logger.info(f"User logged out: {current_user.username}")

    return {"message": "Successfully logged out"}
