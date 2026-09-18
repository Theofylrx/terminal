"""
Position Model
Represents an open or closed trading position
"""

from sqlalchemy import Column, String, Float, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum
from .base_model import BaseModel


class PositionStatus(str, enum.Enum):
    """Position status."""
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    LIQUIDATED = "LIQUIDATED"


class PositionSide(str, enum.Enum):
    """Position side (direction)."""
    LONG = "LONG"
    SHORT = "SHORT"


class AssetClass(str, enum.Enum):
    """Asset class type."""
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"
    COMMODITY = "COMMODITY"


class Position(BaseModel):
    """
    Position model representing a trading position.

    Attributes:
        user_id: User who owns this position
        symbol: Trading symbol (e.g., "BTCUSDT", "AAPL", "EUR_USD")
        asset_class: Asset type (STOCK, CRYPTO, FOREX)
        side: Position direction (LONG, SHORT)
        status: Position status (OPEN, CLOSED, LIQUIDATED)
        quantity: Number of units
        avg_entry_price: Average entry price
        current_price: Latest market price
        market_value: Current market value (quantity * current_price)
        cost_basis: Total cost to enter position
        unrealized_pnl: Unrealized profit/loss
        realized_pnl: Realized profit/loss (for closed positions)
        stop_loss_price: Stop loss trigger price
        take_profit_price: Take profit trigger price
        broker: Broker where position is held
        strategy_id: Strategy that opened this position
    """

    __tablename__ = "positions"

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Position details
    symbol = Column(String(20), nullable=False, index=True)
    asset_class = Column(SQLEnum(AssetClass), nullable=False)
    side = Column(SQLEnum(PositionSide), nullable=False)
    status = Column(SQLEnum(PositionStatus), nullable=False, default=PositionStatus.OPEN, index=True)

    # Quantities and prices
    quantity = Column(Float, nullable=False)
    avg_entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    cost_basis = Column(Float, nullable=False)

    # P&L
    unrealized_pnl = Column(Float, nullable=True, default=0.0)
    realized_pnl = Column(Float, nullable=True, default=0.0)

    # Risk management
    stop_loss_price = Column(Float, nullable=True)
    take_profit_price = Column(Float, nullable=True)

    # Metadata
    broker = Column(String(50), nullable=False)
    strategy_id = Column(String(36), nullable=True)

    # Relationships
    user = relationship("User", back_populates="positions")
    orders = relationship("Order", back_populates="position")

    # Indexes
    __table_args__ = (
        Index('idx_user_symbol_status', 'user_id', 'symbol', 'status'),
        Index('idx_asset_class_status', 'asset_class', 'status'),
    )

    def calculate_unrealized_pnl(self) -> float:
        """
        Calculate unrealized P&L based on current price.

        Returns:
            Unrealized profit/loss

        Example:
            pnl = position.calculate_unrealized_pnl()
        """
        if not self.current_price:
            return 0.0

        if self.side == PositionSide.LONG:
            return (self.current_price - self.avg_entry_price) * self.quantity
        else:  # SHORT
            return (self.avg_entry_price - self.current_price) * self.quantity

    def calculate_pnl_percentage(self) -> float:
        """
        Calculate P&L as percentage of cost basis.

        Returns:
            P&L percentage

        Example:
            pnl_pct = position.calculate_pnl_percentage()
            # Returns: 5.5 for 5.5% gain
        """
        if not self.cost_basis or self.cost_basis == 0:
            return 0.0

        pnl = self.unrealized_pnl if self.status == PositionStatus.OPEN else self.realized_pnl
        return (pnl / self.cost_basis) * 100

    def is_stop_loss_triggered(self) -> bool:
        """
        Check if stop loss price has been hit.

        Returns:
            True if stop loss triggered, False otherwise
        """
        if not self.stop_loss_price or not self.current_price:
            return False

        if self.side == PositionSide.LONG:
            return self.current_price <= self.stop_loss_price
        else:  # SHORT
            return self.current_price >= self.stop_loss_price

    def is_take_profit_triggered(self) -> bool:
        """
        Check if take profit price has been hit.

        Returns:
            True if take profit triggered, False otherwise
        """
        if not self.take_profit_price or not self.current_price:
            return False

        if self.side == PositionSide.LONG:
            return self.current_price >= self.take_profit_price
        else:  # SHORT
            return self.current_price <= self.take_profit_price

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Position(id={self.id}, symbol={self.symbol}, "
            f"side={self.side}, quantity={self.quantity}, "
            f"unrealized_pnl={self.unrealized_pnl})>"
        )
