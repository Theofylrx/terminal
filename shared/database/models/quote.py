"""
Quote Model
Represents bid/ask pricing data
Uses TimescaleDB hypertable for efficient time-series storage
"""

from sqlalchemy import Column, String, Float, DateTime, Index
from .base_model import Base


class Quote(Base):
    """
    Quote (bid/ask) data model.
    Stores real-time pricing information.

    Attributes:
        symbol: Trading symbol
        timestamp: Quote timestamp
        bid_price: Best bid price
        bid_size: Size at bid
        ask_price: Best ask price
        ask_size: Size at ask
        spread: Bid-ask spread (calculated)
        exchange: Exchange or venue identifier
        source: Data source (binance, alpaca, oanda, etc.)
    """

    __tablename__ = "quotes"

    # Composite primary key
    symbol = Column(String(20), primary_key=True, nullable=False)
    timestamp = Column(DateTime, primary_key=True, nullable=False)
    source = Column(String(50), primary_key=True, nullable=False)

    # Bid/Ask data
    bid_price = Column(Float, nullable=False)
    bid_size = Column(Float, nullable=False)
    ask_price = Column(Float, nullable=False)
    ask_size = Column(Float, nullable=False)

    # Calculated fields
    spread = Column(Float, nullable=True)  # ask_price - bid_price

    # Metadata
    exchange = Column(String(50), nullable=True)

    # Indexes for fast queries
    __table_args__ = (
        Index('idx_quote_symbol_timestamp', 'symbol', 'timestamp'),
        Index('idx_quote_timestamp', 'timestamp'),
    )

    def calculate_spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask_price - self.bid_price

    def calculate_mid_price(self) -> float:
        """Calculate mid price."""
        return (self.bid_price + self.ask_price) / 2

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "bid_price": self.bid_price,
            "bid_size": self.bid_size,
            "ask_price": self.ask_price,
            "ask_size": self.ask_size,
            "spread": self.spread or self.calculate_spread(),
            "mid_price": self.calculate_mid_price(),
            "exchange": self.exchange,
            "source": self.source,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Quote(symbol={self.symbol}, timestamp={self.timestamp}, "
            f"bid={self.bid_price}, ask={self.ask_price})>"
        )


# Note: After creating the table, convert it to a hypertable with TimescaleDB:
# SQL: SELECT create_hypertable('quotes', 'timestamp', if_not_exists => TRUE);
