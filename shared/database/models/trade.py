"""
Trade Model
Represents individual trade executions (tape data)
Uses TimescaleDB hypertable for efficient time-series storage
"""

from sqlalchemy import Column, String, Float, DateTime, Index, BigInteger, JSON
from .base_model import Base


class Trade(Base):
    """
    Trade (time and sales) data model.
    Stores individual trade executions.

    Attributes:
        symbol: Trading symbol
        timestamp: Trade execution timestamp
        trade_id: Unique trade identifier from source
        price: Execution price
        size: Execution size/quantity
        side: Trade side (buy/sell) if available
        exchange: Exchange or venue identifier
        conditions: Trade conditions or flags
        source: Data source (binance, alpaca, oanda, etc.)
    """

    __tablename__ = "trades"

    # Composite primary key
    symbol = Column(String(20), primary_key=True, nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    trade_id = Column(String(100), primary_key=True, nullable=False)

    # Trade data
    price = Column(Float, nullable=False)
    size = Column(Float, nullable=False)

    # Optional metadata
    side = Column(String(10), nullable=True)  # buy, sell, or null
    exchange = Column(String(50), nullable=True)
    conditions = Column(JSON, nullable=True)  # Trade conditions/flags

    # Metadata
    source = Column(String(50), nullable=False)

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_trade_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_trade_timestamp', 'timestamp'),
    )

    def calculate_notional(self) -> float:
        """Calculate notional value (price * size)."""
        return self.price * self.size

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "trade_id": self.trade_id,
            "price": self.price,
            "size": self.size,
            "notional": self.calculate_notional(),
            "side": self.side,
            "exchange": self.exchange,
            "conditions": self.conditions,
            "source": self.source,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Trade(symbol={self.symbol}, timestamp={self.timestamp}, "
            f"price={self.price}, size={self.size})>"
        )


# Note: After creating the table, convert it to a hypertable with TimescaleDB:
# SQL: SELECT create_hypertable('trades', 'timestamp', if_not_exists => TRUE);
