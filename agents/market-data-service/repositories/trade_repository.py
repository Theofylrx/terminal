"""Trade (time and sales) data repository."""

import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from shared.database.models import Trade


class TradeRepository:
    """
    Repository for Trade (time and sales) data operations.

    Handles storage and retrieval of individual trade executions.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        symbol: str,
        timestamp: datetime,
        trade_id: str,
        price: float,
        size: float,
        source: str,
        side: Optional[str] = None,
        exchange: Optional[str] = None,
        conditions: Optional[dict] = None,
    ) -> Trade:
        """
        Create a new trade.

        Args:
            symbol: Trading symbol.
            timestamp: Trade timestamp.
            trade_id: Unique trade ID from source.
            price: Execution price.
            size: Execution size.
            source: Data source.
            side: Trade side (buy/sell).
            exchange: Exchange identifier.
            conditions: Trade conditions/flags.

        Returns:
            Created Trade object.
        """
        trade = Trade(
            symbol=symbol,
            timestamp=timestamp,
            trade_id=trade_id,
            price=price,
            size=size,
            side=side,
            exchange=exchange,
            conditions=conditions,
            source=source,
        )
        self.session.add(trade)
        await self.session.commit()
        await self.session.refresh(trade)
        return trade

    async def upsert(
        self,
        symbol: str,
        timestamp: datetime,
        trade_id: str,
        price: float,
        size: float,
        source: str,
        side: Optional[str] = None,
        exchange: Optional[str] = None,
        conditions: Optional[dict] = None,
    ) -> Trade:
        """Insert or update trade (handles duplicates)."""
        stmt = insert(Trade).values(
            symbol=symbol,
            timestamp=timestamp,
            trade_id=trade_id,
            price=price,
            size=size,
            side=side,
            exchange=exchange,
            conditions=conditions,
            source=source,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timestamp", "trade_id"],
            set_={
                "price": price,
                "size": size,
                "side": side,
                "exchange": exchange,
                "conditions": conditions,
            },
        )

        await self.session.execute(stmt)
        await self.session.commit()

        return await self.get(symbol, timestamp, trade_id)

    async def get(
        self, symbol: str, timestamp: datetime, trade_id: str
    ) -> Optional[Trade]:
        """Get specific trade by composite key."""
        query = select(Trade).where(
            and_(
                Trade.symbol == symbol,
                Trade.timestamp == timestamp,
                Trade.trade_id == trade_id,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest(
        self, symbol: str, source: Optional[str] = None, limit: int = 100
    ) -> List[Trade]:
        """Get most recent trades for symbol."""
        query = select(Trade).where(Trade.symbol == symbol)

        if source:
            query = query.where(Trade.source == source)

        query = query.order_by(Trade.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Trade]:
        """Get trades for a time range."""
        query = select(Trade).where(
            and_(
                Trade.symbol == symbol,
                Trade.timestamp >= start,
                Trade.timestamp <= end,
            )
        )

        if source:
            query = query.where(Trade.source == source)

        query = query.order_by(Trade.timestamp.asc())

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_old_data(self, before: datetime) -> int:
        """Delete trades older than specified date."""
        stmt = delete(Trade).where(Trade.timestamp < before)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def count(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Count trades matching criteria."""
        query = select(func.count()).select_from(Trade)

        conditions = []
        if symbol:
            conditions.append(Trade.symbol == symbol)
        if start:
            conditions.append(Trade.timestamp >= start)
        if end:
            conditions.append(Trade.timestamp <= end)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()

    async def get_volume(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        source: Optional[str] = None,
    ) -> float:
        """Calculate total trading volume for period."""
        query = select(func.sum(Trade.size)).where(
            and_(
                Trade.symbol == symbol,
                Trade.timestamp >= start,
                Trade.timestamp <= end,
            )
        )

        if source:
            query = query.where(Trade.source == source)

        result = await self.session.execute(query)
        volume = result.scalar()
        return float(volume) if volume else 0.0
