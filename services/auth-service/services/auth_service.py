"""
Authentication Service
Business logic for user authentication and authorization
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt

import sys
sys.path.append('/app')

from shared.database.models.user import User
from services.auth_service.repositories.user_repository import UserRepository
from services.auth_service.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Authentication service handling user registration, login, and token management.
    """

    def __init__(self, user_repo: UserRepository):
        """
        Initialize auth service.

        Args:
            user_repo: User repository for data access
        """
        self.user_repo = user_repo

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password

        Example:
            hashed = AuthService.hash_password("mypassword123")
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.

        Args:
            plain_password: Plain text password
            hashed_password: Bcrypt hash

        Returns:
            True if password matches, False otherwise

        Example:
            is_valid = AuthService.verify_password("password", user.hashed_password)
        """
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT access token.

        Args:
            data: Token payload
            expires_delta: Optional custom expiration

        Returns:
            Encoded JWT token

        Example:
            token = AuthService.create_access_token({"sub": user.id, "email": user.email})
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token (longer expiration).

        Args:
            data: Token payload

        Returns:
            Encoded JWT refresh token

        Example:
            refresh = AuthService.create_refresh_token({"sub": user.id})
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })

        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )

        return encoded_jwt

    async def register_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        initial_capital: Optional[float] = None
    ) -> User:
        """
        Register new user.

        Args:
            email: User email
            username: Username
            password: Plain text password
            first_name: Optional first name
            last_name: Optional last name
            initial_capital: Optional starting capital

        Returns:
            Created user

        Raises:
            HTTPException: If email or username already exists

        Example:
            user = await auth_service.register_user(
                email="trader@example.com",
                username="trader1",
                password="securepass123",
                initial_capital=10000.0
            )
        """
        # Check if email exists
        if await self.user_repo.email_exists(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username exists
        if await self.user_repo.username_exists(username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        hashed_password = self.hash_password(password)

        # Create user
        user = await self.user_repo.create_user(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            initial_capital=initial_capital
        )

        return user

    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Authenticated user

        Raises:
            HTTPException: If credentials are invalid

        Example:
            user = await auth_service.authenticate_user("trader@example.com", "password")
        """
        # Get user by email
        user = await self.user_repo.get_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify password
        if not self.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Update last login
        await self.user_repo.update_last_login(user.id)

        return user

    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user and generate tokens.

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dictionary with access_token, refresh_token, and user data

        Example:
            result = await auth_service.login("trader@example.com", "password")
            access_token = result["access_token"]
        """
        # Authenticate user
        user = await self.authenticate_user(email, password)

        # Create token payload
        token_data = {
            "sub": user.id,
            "email": user.email,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser
        }

        # Generate tokens
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": user.id})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRATION_MINUTES * 60,  # seconds
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "current_capital": user.current_capital
            }
        }

    async def refresh_access_token(self, refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            HTTPException: If refresh token is invalid

        Example:
            result = await auth_service.refresh_access_token(refresh_token)
            new_access_token = result["access_token"]
        """
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Get user
            user_id = payload.get("sub")
            user = await self.user_repo.get_by_id(user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )

            # Check if user is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is inactive"
                )

            # Create new access token
            token_data = {
                "sub": user.id,
                "email": user.email,
                "username": user.username,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser
            }

            access_token = self.create_access_token(token_data)

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.JWT_EXPIRATION_MINUTES * 60
            }

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def get_user_by_id(self, user_id: str) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User

        Raises:
            HTTPException: If user not found

        Example:
            user = await auth_service.get_user_by_id("user-123")
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user
