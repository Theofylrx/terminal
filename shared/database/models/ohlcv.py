"""
OHLCV Model
Represents candlestick/bar data (Open, High, Low, Close, Volume)
Uses TimescaleDB hypertable for efficient time-series storage
"""

from sqlalchemy import Column, String, Float, DateTime, Index, BigInteger
from .base_model import Base  # Don't inherit from BaseModel for time-series data


class OHLCV(Base):
    """
    OHLCV (candlestick) data model.
    Optimized for time-series data with TimescaleDB.

    Attributes:
        symbol: Trading symbol
        timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1D, etc.)
        timestamp: Candle timestamp (opening time)
        open: Opening price
        high: Highest price
        low: Lowest price
        close: Closing price
        volume: Trading volume
        quote_volume: Quote asset volume
        num_trades: Number of trades in this candle
        source: Data source (binance, alpaca, oanda, etc.)
    """

    __tablename__ = "ohlcv"

    # Composite primary key
    symbol = Column(String(20), primary_key=True, nullable=False)
    timeframe = Column(String(10), primary_key=True, nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False)

    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Additional data
    quote_volume = Column(Float, nullable=True)  # Volume in quote currency
    num_trades = Column(BigInteger, nullable=True)  # Number of trades

    # Metadata
    source = Column(String(50), nullable=False)  # binance, alpaca, etc.

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_symbol_timeframe_timestamp', 'symbol', 'timeframe', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )

    def to_dict(self) -> dict:
        """
        Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "quote_volume": self.quote_volume,
            "num_trades": self.num_trades,
            "source": self.source
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<OHLCV(symbol={self.symbol}, timeframe={self.timeframe}, "
            f"timestamp={self.timestamp}, close={self.close})>"
        )


# Note: After creating the table, convert it to a hypertable with TimescaleDB:
# SQL: SELECT create_hypertable('ohlcv', 'timestamp', if_not_exists => TRUE);
