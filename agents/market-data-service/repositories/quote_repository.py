"""Quote (bid/ask) data repository."""

import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from shared.database.models import Quote


class QuoteRepository:
    """
    Repository for Quote (bid/ask) data operations.

    Handles storage and retrieval of real-time pricing data.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        symbol: str,
        timestamp: datetime,
        bid_price: float,
        bid_size: float,
        ask_price: float,
        ask_size: float,
        source: str,
        exchange: Optional[str] = None,
    ) -> Quote:
        """
        Create a new quote.

        Args:
            symbol: Trading symbol.
            timestamp: Quote timestamp.
            bid_price: Best bid price.
            bid_size: Size at bid.
            ask_price: Best ask price.
            ask_size: Size at ask.
            source: Data source.
            exchange: Exchange identifier.

        Returns:
            Created Quote object.
        """
        spread = ask_price - bid_price

        quote = Quote(
            symbol=symbol,
            timestamp=timestamp,
            bid_price=bid_price,
            bid_size=bid_size,
            ask_price=ask_price,
            ask_size=ask_size,
            spread=spread,
            exchange=exchange,
            source=source,
        )
        self.session.add(quote)
        await self.session.commit()
        await self.session.refresh(quote)
        return quote

    async def upsert(
        self,
        symbol: str,
        timestamp: datetime,
        bid_price: float,
        bid_size: float,
        ask_price: float,
        ask_size: float,
        source: str,
        exchange: Optional[str] = None,
    ) -> Quote:
        """Insert or update quote (handles duplicates)."""
        spread = ask_price - bid_price

        stmt = insert(Quote).values(
            symbol=symbol,
            timestamp=timestamp,
            bid_price=bid_price,
            bid_size=bid_size,
            ask_price=ask_price,
            ask_size=ask_size,
            spread=spread,
            exchange=exchange,
            source=source,
        )

        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timestamp", "source"],
            set_={
                "bid_price": bid_price,
                "bid_size": bid_size,
                "ask_price": ask_price,
                "ask_size": ask_size,
                "spread": spread,
                "exchange": exchange,
            },
        )

        await self.session.execute(stmt)
        await self.session.commit()

        return await self.get(symbol, timestamp, source)

    async def get(
        self, symbol: str, timestamp: datetime, source: str
    ) -> Optional[Quote]:
        """Get specific quote by composite key."""
        query = select(Quote).where(
            and_(
                Quote.symbol == symbol,
                Quote.timestamp == timestamp,
                Quote.source == source,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest(self, symbol: str, source: Optional[str] = None) -> Optional[Quote]:
        """Get most recent quote for symbol."""
        query = select(Quote).where(Quote.symbol == symbol)

        if source:
            query = query.where(Quote.source == source)

        query = query.order_by(Quote.timestamp.desc()).limit(1)

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        source: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Quote]:
        """Get quotes for a time range."""
        query = select(Quote).where(
            and_(
                Quote.symbol == symbol,
                Quote.timestamp >= start,
                Quote.timestamp <= end,
            )
        )

        if source:
            query = query.where(Quote.source == source)

        query = query.order_by(Quote.timestamp.asc())

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_old_data(self, before: datetime) -> int:
        """Delete quotes older than specified date."""
        stmt = delete(Quote).where(Quote.timestamp < before)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def count(
        self,
        symbol: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Count quotes matching criteria."""
        query = select(func.count()).select_from(Quote)

        conditions = []
        if symbol:
            conditions.append(Quote.symbol == symbol)
        if start:
            conditions.append(Quote.timestamp >= start)
        if end:
            conditions.append(Quote.timestamp <= end)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()
