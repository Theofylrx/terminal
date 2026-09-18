"""
User Repository
Data access layer for User model with authentication-specific queries
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.append('/app')

from shared.database.base_repository import BaseRepository
from shared.database.models.user import User


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with authentication methods.
    Extends BaseRepository for common CRUD operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize user repository.

        Args:
            session: Async database session
        """
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User if found, None otherwise

        Example:
            user = await user_repo.get_by_email("trader@example.com")
        """
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username

        Returns:
            User if found, None otherwise

        Example:
            user = await user_repo.get_by_username("trader1")
        """
        query = select(User).where(User.username == username)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email to check

        Returns:
            True if email exists, False otherwise

        Example:
            exists = await user_repo.email_exists("new@example.com")
        """
        return await self.exists(email=email)

    async def username_exists(self, username: str) -> bool:
        """
        Check if username is already taken.

        Args:
            username: Username to check

        Returns:
            True if username exists, False otherwise

        Example:
            exists = await user_repo.username_exists("newtrader")
        """
        return await self.exists(username=username)

    async def create_user(
        self,
        email: str,
        username: str,
        hashed_password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        initial_capital: Optional[float] = None
    ) -> User:
        """
        Create new user with hashed password.

        Args:
            email: User email
            username: Username
            hashed_password: Bcrypt hashed password
            first_name: Optional first name
            last_name: Optional last name
            initial_capital: Optional starting capital

        Returns:
            Created user

        Example:
            user = await user_repo.create_user(
                email="trader@example.com",
                username="trader1",
                hashed_password=hashed,
                initial_capital=10000.0
            )
        """
        return await self.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            initial_capital=initial_capital,
            current_capital=initial_capital,  # Start with initial capital
            is_active=True,
            is_verified=False,  # Require email verification
            is_superuser=False
        )

    async def update_last_login(self, user_id: str) -> Optional[User]:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID

        Returns:
            Updated user

        Example:
            user = await user_repo.update_last_login(user_id)
        """
        from datetime import datetime
        return await self.update(user_id, last_login=datetime.utcnow())

    async def activate_user(self, user_id: str) -> Optional[User]:
        """
        Activate user account.

        Args:
            user_id: User ID

        Returns:
            Updated user

        Example:
            user = await user_repo.activate_user(user_id)
        """
        return await self.update(user_id, is_active=True)

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """
        Deactivate user account.

        Args:
            user_id: User ID

        Returns:
            Updated user

        Example:
            user = await user_repo.deactivate_user(user_id)
        """
        return await self.update(user_id, is_active=False)

    async def verify_email(self, user_id: str) -> Optional[User]:
        """
        Mark user email as verified.

        Args:
            user_id: User ID

        Returns:
            Updated user

        Example:
            user = await user_repo.verify_email(user_id)
        """
        return await self.update(user_id, is_verified=True)
