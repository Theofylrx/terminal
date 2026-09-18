"""
Authentication Routes
API endpoints for user authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.append('/app')

from shared.database.connection import get_db_session
from services.auth_service.repositories.user_repository import UserRepository
from services.auth_service.services.auth_service import AuthService
from services.auth_service.api.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    RefreshTokenRequest,
    UserResponse,
    LoginResponse,
    TokenResponse,
    MessageResponse
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(session: AsyncSession = Depends(get_db_session)) -> AuthService:
    """
    Dependency injection for AuthService.

    Args:
        session: Database session

    Returns:
        AuthService instance
    """
    user_repo = UserRepository(session)
    return AuthService(user_repo)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: UserRegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user.

    Args:
        request: User registration data
        auth_service: Auth service instance

    Returns:
        Created user data (without password)

    Raises:
        400: Email or username already exists
        422: Validation error

    Example Request:
    ```json
    {
        "email": "trader@example.com",
        "username": "trader1",
        "password": "SecurePass123",
        "first_name": "John",
        "last_name": "Doe",
        "initial_capital": 10000.0
    }
    ```

    Example Response:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "trader@example.com",
        "username": "trader1",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_verified": false,
        "is_superuser": false,
        "current_capital": 10000.0,
        "created_at": "2024-01-01T00:00:00Z"
    }
    ```
    """
    user = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
        initial_capital=request.initial_capital
    )

    return UserResponse.from_orm(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    request: UserLoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login user and get access tokens.

    Args:
        request: Login credentials
        auth_service: Auth service instance

    Returns:
        Access token, refresh token, and user data

    Raises:
        401: Invalid credentials
        403: User account is inactive

    Example Request:
    ```json
    {
        "email": "trader@example.com",
        "password": "SecurePass123"
    }
    ```

    Example Response:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "trader@example.com",
            "username": "trader1",
            "is_active": true
        }
    }
    ```
    """
    result = await auth_service.login(request.email, request.password)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token
        auth_service: Auth service instance

    Returns:
        New access token

    Raises:
        401: Invalid or expired refresh token

    Example Request:
    ```json
    {
        "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
    }
    ```

    Example Response:
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIs...",
        "token_type": "bearer",
        "expires_in": 1800
    }
    ```
    """
    result = await auth_service.refresh_access_token(request.refresh_token)
    return result


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    user_id: str = Depends(lambda: "user-id-from-jwt"),  # TODO: Get from JWT in gateway
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get current authenticated user.

    Note: In production, user_id would be extracted from JWT token
    by the API Gateway and passed via X-User-ID header.

    Args:
        user_id: User ID from JWT token
        auth_service: Auth service instance

    Returns:
        Current user data

    Raises:
        401: Not authenticated
        404: User not found

    Example Response:
    ```json
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "trader@example.com",
        "username": "trader1",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": true,
        "is_verified": true,
        "current_capital": 9500.0,
        "last_login": "2024-01-01T12:00:00Z"
    }
    ```
    """
    user = await auth_service.get_user_by_id(user_id)
    return UserResponse.from_orm(user)


@router.get("/health", response_model=MessageResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        Service health status
    """
    return MessageResponse(
        message="Auth Service is healthy",
        detail="All systems operational"
    )
