"""
Auto-Trading Configuration Repository
Handles database operations for auto-trading configs
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database.models.auto_trading_config import AutoTradingConfig


class AutoTradingConfigRepository:
    """Repository for auto-trading configuration operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, config: AutoTradingConfig) -> AutoTradingConfig:
        """
        Create new auto-trading configuration.

        Args:
            config: AutoTradingConfig instance

        Returns:
            Created configuration
        """
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def get_by_id(self, config_id: str) -> Optional[AutoTradingConfig]:
        """
        Get configuration by ID.

        Args:
            config_id: Configuration ID

        Returns:
            Configuration if found, None otherwise
        """
        result = await self.session.execute(
            select(AutoTradingConfig).where(AutoTradingConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_symbol(
        self, user_id: str, symbol: str
    ) -> Optional[AutoTradingConfig]:
        """
        Get configuration for specific user and symbol.

        Args:
            user_id: User ID
            symbol: Trading symbol

        Returns:
            Configuration if found, None otherwise
        """
        result = await self.session.execute(
            select(AutoTradingConfig).where(
                and_(
                    AutoTradingConfig.user_id == user_id,
                    AutoTradingConfig.symbol == symbol
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_all_enabled(self) -> List[AutoTradingConfig]:
        """
        Get all enabled auto-trading configurations.

        Returns:
            List of enabled configurations
        """
        result = await self.session.execute(
            select(AutoTradingConfig).where(AutoTradingConfig.enabled == True)
        )
        return list(result.scalars().all())

    async def get_enabled_by_user(self, user_id: str) -> List[AutoTradingConfig]:
        """
        Get all enabled configurations for a user.

        Args:
            user_id: User ID

        Returns:
            List of user's enabled configurations
        """
        result = await self.session.execute(
            select(AutoTradingConfig).where(
                and_(
                    AutoTradingConfig.user_id == user_id,
                    AutoTradingConfig.enabled == True
                )
            )
        )
        return list(result.scalars().all())

    async def get_all_by_user(self, user_id: str) -> List[AutoTradingConfig]:
        """
        Get all configurations for a user (enabled and disabled).

        Args:
            user_id: User ID

        Returns:
            List of user's configurations
        """
        result = await self.session.execute(
            select(AutoTradingConfig).where(AutoTradingConfig.user_id == user_id)
        )
        return list(result.scalars().all())

    async def update(self, config: AutoTradingConfig) -> AutoTradingConfig:
        """
        Update configuration.

        Args:
            config: Configuration to update

        Returns:
            Updated configuration
        """
        await self.session.commit()
        await self.session.refresh(config)
        return config

    async def enable(self, config_id: str) -> Optional[AutoTradingConfig]:
        """
        Enable auto-trading for a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Updated configuration if found
        """
        config = await self.get_by_id(config_id)
        if config:
            config.enabled = True
            return await self.update(config)
        return None

    async def disable(self, config_id: str) -> Optional[AutoTradingConfig]:
        """
        Disable auto-trading for a configuration.

        Args:
            config_id: Configuration ID

        Returns:
            Updated configuration if found
        """
        config = await self.get_by_id(config_id)
        if config:
            config.enabled = False
            return await self.update(config)
        return None

    async def delete(self, config_id: str) -> bool:
        """
        Delete configuration.

        Args:
            config_id: Configuration ID

        Returns:
            True if deleted, False if not found
        """
        config = await self.get_by_id(config_id)
        if config:
            await self.session.delete(config)
            await self.session.commit()
            return True
        return False
