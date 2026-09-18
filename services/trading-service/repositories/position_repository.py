"""
Position Repository
Data access layer for Position model with trading-specific queries
"""

from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

import sys
sys.path.append('/app')

from shared.database.base_repository import BaseRepository
from shared.database.models.position import Position, PositionStatus, PositionSide, AssetClass


class PositionRepository(BaseRepository[Position]):
    """
    Repository for Position model with trading operations.
    Extends BaseRepository for common CRUD operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize position repository.

        Args:
            session: Async database session
        """
        super().__init__(Position, session)

    async def get_open_positions(self, user_id: str) -> List[Position]:
        """
        Get all open positions for a user.

        Args:
            user_id: User ID

        Returns:
            List of open positions

        Example:
            positions = await position_repo.get_open_positions("user-123")
        """
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN
            )
        ).order_by(Position.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_position_by_symbol(
        self,
        user_id: str,
        symbol: str
    ) -> Optional[Position]:
        """
        Get open position by symbol.

        Args:
            user_id: User ID
            symbol: Trading symbol

        Returns:
            Position if found, None otherwise

        Example:
            position = await position_repo.get_position_by_symbol("user-123", "BTCUSDT")
        """
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.symbol == symbol,
                Position.status == PositionStatus.OPEN
            )
        )

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_positions_by_asset_class(
        self,
        user_id: str,
        asset_class: AssetClass
    ) -> List[Position]:
        """
        Get all open positions for specific asset class.

        Args:
            user_id: User ID
            asset_class: Asset class (STOCK, CRYPTO, FOREX)

        Returns:
            List of positions

        Example:
            positions = await position_repo.get_positions_by_asset_class("user-123", AssetClass.CRYPTO)
        """
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.asset_class == asset_class,
                Position.status == PositionStatus.OPEN
            )
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_exposure(self, user_id: str) -> float:
        """
        Calculate total market value of all open positions.

        Args:
            user_id: User ID

        Returns:
            Total exposure in USD

        Example:
            exposure = await position_repo.get_total_exposure("user-123")
        """
        query = select(func.sum(Position.market_value)).where(
            and_(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN
            )
        )

        result = await self.session.execute(query)
        total = result.scalar_one_or_none()
        return total or 0.0

    async def get_total_unrealized_pnl(self, user_id: str) -> float:
        """
        Calculate total unrealized P&L across all open positions.

        Args:
            user_id: User ID

        Returns:
            Total unrealized P&L in USD

        Example:
            pnl = await position_repo.get_total_unrealized_pnl("user-123")
        """
        query = select(func.sum(Position.unrealized_pnl)).where(
            and_(
                Position.user_id == user_id,
                Position.status == PositionStatus.OPEN
            )
        )

        result = await self.session.execute(query)
        total = result.scalar_one_or_none()
        return total or 0.0

    async def get_position_count(self, user_id: str) -> int:
        """
        Get count of open positions.

        Args:
            user_id: User ID

        Returns:
            Number of open positions

        Example:
            count = await position_repo.get_position_count("user-123")
        """
        return await self.count(user_id=user_id, status=PositionStatus.OPEN)

    async def update_position_price(
        self,
        position_id: str,
        current_price: float
    ) -> Optional[Position]:
        """
        Update position with latest market price and recalculate P&L.

        Args:
            position_id: Position ID
            current_price: Latest market price

        Returns:
            Updated position

        Example:
            position = await position_repo.update_position_price("pos-123", 50100.0)
        """
        # Get position
        position = await self.get_by_id(position_id)
        if not position:
            return None

        # Calculate market value
        market_value = current_price * position.quantity

        # Calculate unrealized P&L
        if position.side == PositionSide.LONG:
            unrealized_pnl = (current_price - position.avg_entry_price) * position.quantity
        else:  # SHORT
            unrealized_pnl = (position.avg_entry_price - current_price) * position.quantity

        # Update position
        return await self.update(
            position_id,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl
        )

    async def close_position(
        self,
        position_id: str,
        close_price: float
    ) -> Optional[Position]:
        """
        Close position and calculate realized P&L.

        Args:
            position_id: Position ID
            close_price: Closing price

        Returns:
            Closed position

        Example:
            position = await position_repo.close_position("pos-123", 51000.0)
        """
        # Get position
        position = await self.get_by_id(position_id)
        if not position:
            return None

        # Calculate realized P&L
        if position.side == PositionSide.LONG:
            realized_pnl = (close_price - position.avg_entry_price) * position.quantity
        else:  # SHORT
            realized_pnl = (position.avg_entry_price - close_price) * position.quantity

        # Update position
        return await self.update(
            position_id,
            status=PositionStatus.CLOSED,
            current_price=close_price,
            market_value=close_price * position.quantity,
            realized_pnl=realized_pnl,
            unrealized_pnl=0.0
        )

    async def get_closed_positions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Position]:
        """
        Get closed positions (trade history).

        Args:
            user_id: User ID
            limit: Maximum number of positions to return

        Returns:
            List of closed positions

        Example:
            history = await position_repo.get_closed_positions("user-123", limit=50)
        """
        query = select(Position).where(
            and_(
                Position.user_id == user_id,
                Position.status == PositionStatus.CLOSED
            )
        ).order_by(Position.updated_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
