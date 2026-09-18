"""OHLCV (candlestick) data repository."""

import sys
from pathlib import Path

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from shared.database.models import OHLCV


class OHLCVRepository:
    """
    Repository for OHLCV (candlestick) data operations.

    Handles storage and retrieval of time-series bar data
    optimized for TimescaleDB.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        source: str,
        quote_volume: Optional[float] = None,
        num_trades: Optional[int] = None,
    ) -> OHLCV:
        """
        Create a new OHLCV bar.

        Args:
            symbol: Trading symbol.
            timeframe: Bar timeframe (1m, 5m, etc.).
            timestamp: Bar timestamp (opening time).
            open: Opening price.
            high: Highest price.
            low: Lowest price.
            close: Closing price.
            volume: Trading volume.
            source: Data source (alpaca, binance, oanda).
            quote_volume: Quote asset volume.
            num_trades: Number of trades.

        Returns:
            Created OHLCV object.
        """
        bar = OHLCV(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            source=source,
            quote_volume=quote_volume,
            num_trades=num_trades,
        )
        self.session.add(bar)
        await self.session.commit()
        await self.session.refresh(bar)
        return bar

    async def upsert(
        self,
        symbol: str,
        timeframe: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        source: str,
        quote_volume: Optional[float] = None,
        num_trades: Optional[int] = None,
    ) -> OHLCV:
        """
        Insert or update OHLCV bar (handles duplicates).

        Args:
            Same as create().

        Returns:
            OHLCV object.
        """
        stmt = insert(OHLCV).values(
            symbol=symbol,
            timeframe=timeframe,
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            source=source,
            quote_volume=quote_volume,
            num_trades=num_trades,
        )

        # On conflict, update all fields except primary keys
        stmt = stmt.on_conflict_do_update(
            index_elements=["symbol", "timeframe", "timestamp"],
            set_={
                "open": open,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "quote_volume": quote_volume,
                "num_trades": num_trades,
            },
        )

        await self.session.execute(stmt)
        await self.session.commit()

        # Fetch and return the bar
        return await self.get(symbol, timeframe, timestamp)

    async def get(
        self, symbol: str, timeframe: str, timestamp: datetime
    ) -> Optional[OHLCV]:
        """Get specific OHLCV bar by composite key."""
        query = select(OHLCV).where(
            and_(
                OHLCV.symbol == symbol,
                OHLCV.timeframe == timeframe,
                OHLCV.timestamp == timestamp,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_range(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[OHLCV]:
        """
        Get OHLCV bars for a time range.

        Args:
            symbol: Trading symbol.
            timeframe: Bar timeframe.
            start: Start datetime (inclusive).
            end: End datetime (inclusive).
            limit: Maximum bars to return.

        Returns:
            List of OHLCV bars ordered by timestamp.
        """
        query = (
            select(OHLCV)
            .where(
                and_(
                    OHLCV.symbol == symbol,
                    OHLCV.timeframe == timeframe,
                    OHLCV.timestamp >= start,
                    OHLCV.timestamp <= end,
                )
            )
            .order_by(OHLCV.timestamp.asc())
        )

        if limit:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, symbol: str, timeframe: str) -> Optional[OHLCV]:
        """Get most recent OHLCV bar for symbol and timeframe."""
        query = (
            select(OHLCV)
            .where(and_(OHLCV.symbol == symbol, OHLCV.timeframe == timeframe))
            .order_by(OHLCV.timestamp.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_bars(
        self, symbols: List[str], timeframe: str, limit: int = 100
    ) -> List[OHLCV]:
        """
        Get latest N bars for multiple symbols.

        Args:
            symbols: List of symbols.
            timeframe: Bar timeframe.
            limit: Bars per symbol.

        Returns:
            List of latest OHLCV bars.
        """
        query = (
            select(OHLCV)
            .where(and_(OHLCV.symbol.in_(symbols), OHLCV.timeframe == timeframe))
            .order_by(OHLCV.symbol.asc(), OHLCV.timestamp.desc())
            .limit(limit * len(symbols))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def delete_old_data(self, before: datetime) -> int:
        """
        Delete OHLCV data older than specified date.

        Args:
            before: Delete data before this datetime.

        Returns:
            Number of rows deleted.
        """
        stmt = delete(OHLCV).where(OHLCV.timestamp < before)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def count(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> int:
        """Count OHLCV bars matching criteria."""
        query = select(func.count()).select_from(OHLCV)

        conditions = []
        if symbol:
            conditions.append(OHLCV.symbol == symbol)
        if timeframe:
            conditions.append(OHLCV.timeframe == timeframe)
        if start:
            conditions.append(OHLCV.timestamp >= start)
        if end:
            conditions.append(OHLCV.timestamp <= end)

        if conditions:
            query = query.where(and_(*conditions))

        result = await self.session.execute(query)
        return result.scalar()
