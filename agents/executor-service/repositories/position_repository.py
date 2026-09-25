"""
Position Repository
Handles database operations for positions
"""

from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

import sys
sys.path.append('/Users/likhobomvana/terminal')

from shared.database.models.position import Position, PositionStatus


class PositionRepository:
    """Repository for position database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, position: Position) -> Position:
        """
        Create new position.

        Args:
            position: Position instance

        Returns:
            Created position
        """
        self.session.add(position)
        await self.session.commit()
        await self.session.refresh(position)
        return position

    async def get_by_id(self, position_id: str) -> Optional[Position]:
        """
        Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position if found, None otherwise
        """
        result = await self.session.execute(
            select(Position).where(Position.id == position_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_symbol(
        self, user_id: str, symbol: str
    ) -> Optional[Position]:
        """
        Get open position for user and symbol.

        Args:
            user_id: User ID
            symbol: Trading symbol

        Returns:
            Position if found, None otherwise
        """
        result = await self.session.execute(
            select(Position).where(
                and_(
                    Position.user_id == user_id,
                    Position.symbol == symbol,
                    Position.status == PositionStatus.OPEN
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_open_positions(self, user_id: str) -> List[Position]:
        """
        Get all open positions for a user.

        Args:
            user_id: User ID

        Returns:
            List of open positions
        """
        result = await self.session.execute(
            select(Position).where(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.OPEN
                )
            )
        )
        return list(result.scalars().all())

    async def get_all_positions(
        self,
        user_id: str,
        status: Optional[PositionStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Position]:
        """
        Get positions for a user with optional filters.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            symbol: Filter by symbol (optional)
            limit: Maximum number of positions

        Returns:
            List of positions
        """
        query = select(Position).where(Position.user_id == user_id)

        if status:
            query = query.where(Position.status == status)

        if symbol:
            query = query.where(Position.symbol == symbol)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_position_price(
        self,
        position_id: str,
        current_price: float
    ) -> Optional[Position]:
        """
        Update position current price and P&L.

        Args:
            position_id: Position ID
            current_price: Current market price

        Returns:
            Updated position or None if not found
        """
        position = await self.get_by_id(position_id)
        if not position:
            return None

        position.current_price = current_price
        position.market_value = position.quantity * current_price
        position.unrealized_pnl = position.calculate_unrealized_pnl()
        position.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(position)
        return position

    async def close_position(
        self,
        position_id: str,
        close_price: float
    ) -> Optional[Position]:
        """
        Close a position.

        Args:
            position_id: Position ID
            close_price: Closing price

        Returns:
            Closed position or None if not found
        """
        position = await self.get_by_id(position_id)
        if not position:
            return None

        position.current_price = close_price
        position.market_value = position.quantity * close_price
        position.status = PositionStatus.CLOSED

        # Move unrealized P&L to realized
        position.realized_pnl = position.calculate_unrealized_pnl()
        position.unrealized_pnl = 0.0

        position.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(position)
        return position

    async def get_daily_pnl(self, user_id: str) -> float:
        """
        Calculate total daily P&L for a user.

        Args:
            user_id: User ID

        Returns:
            Total daily P&L
        """
        # Get all closed positions from today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.session.execute(
            select(func.sum(Position.realized_pnl)).where(
                and_(
                    Position.user_id == user_id,
                    Position.status == PositionStatus.CLOSED,
                    Position.updated_at >= today_start
                )
            )
        )

        closed_pnl = result.scalar() or 0.0

        # Add unrealized P&L from open positions
        open_positions = await self.get_open_positions(user_id)
        open_pnl = sum(pos.unrealized_pnl or 0.0 for pos in open_positions)

        return closed_pnl + open_pnl

    async def get_positions_in_symbol(
        self, user_id: str, symbol: str
    ) -> int:
        """
        Count open positions in a symbol for a user.

        Args:
            user_id: User ID
            symbol: Trading symbol

        Returns:
            Number of open positions
        """
        result = await self.session.execute(
            select(func.count(Position.id)).where(
                and_(
                    Position.user_id == user_id,
                    Position.symbol == symbol,
                    Position.status == PositionStatus.OPEN
                )
            )
        )

        return result.scalar() or 0

    async def delete(self, position_id: str) -> bool:
        """
        Delete a position.

        Args:
            position_id: Position ID

        Returns:
            True if deleted, False if not found
        """
        position = await self.get_by_id(position_id)
        if not position:
            return False

        await self.session.delete(position)
        await self.session.commit()
        return True
