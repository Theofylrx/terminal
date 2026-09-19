"""
Order Model
Represents a trade order (buy/sell)
"""

from sqlalchemy import Column, String, Float, Enum as SQLEnum, ForeignKey, Index, DateTime
from sqlalchemy.orm import relationship
import enum
from .base_model import BaseModel


class OrderType(str, enum.Enum):
    """Order type."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderSide(str, enum.Enum):
    """Order side (buy/sell)."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    """Order status."""
    PENDING = "PENDING"              # Created, not yet submitted
    SUBMITTED = "SUBMITTED"          # Submitted to broker
    ACCEPTED = "ACCEPTED"            # Accepted by broker
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Partial execution
    FILLED = "FILLED"                # Fully executed
    CANCELLED = "CANCELLED"          # Cancelled by user/system
    REJECTED = "REJECTED"            # Rejected by broker
    EXPIRED = "EXPIRED"              # Expired (GTD orders)


class TimeInForce(str, enum.Enum):
    """Time in force."""
    GTC = "GTC"  # Good Till Cancelled
    GTD = "GTD"  # Good Till Date
    IOC = "IOC"  # Immediate Or Cancel
    FOK = "FOK"  # Fill Or Kill
    DAY = "DAY"  # Day order


class Order(BaseModel):
    """
    Order model representing a trade order.

    Attributes:
        user_id: User who created this order
        position_id: Associated position (if any)
        symbol: Trading symbol
        asset_class: Asset type
        order_type: Order type (MARKET, LIMIT, etc.)
        side: BUY or SELL
        status: Order status
        quantity: Number of units to trade
        filled_quantity: Number of units actually filled
        limit_price: Limit price (for LIMIT orders)
        stop_price: Stop price (for STOP orders)
        avg_fill_price: Average fill price
        time_in_force: How long order remains active
        broker_order_id: Order ID from broker
        broker: Broker where order was placed
        strategy_id: Strategy that created this order
        commission: Trading commission/fees
        slippage: Price slippage
        submitted_at: When order was submitted to broker
        filled_at: When order was fully filled
    """

    __tablename__ = "orders"

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    position_id = Column(String(36), ForeignKey("positions.id"), nullable=True, index=True)

    # Broker credential link - tracks which broker account was used
    broker_credential_id = Column(String(36), ForeignKey("broker_credentials.id"), nullable=True, index=True)

    # Order details
    symbol = Column(String(20), nullable=False, index=True)
    asset_class = Column(SQLEnum("AssetClass"), nullable=False)  # Reference from Position model
    order_type = Column(SQLEnum(OrderType), nullable=False)
    side = Column(SQLEnum(OrderSide), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING, index=True)

    # Quantities
    quantity = Column(Float, nullable=False)
    filled_quantity = Column(Float, nullable=False, default=0.0)

    # Prices
    limit_price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    avg_fill_price = Column(Float, nullable=True)

    # Order parameters
    time_in_force = Column(SQLEnum(TimeInForce), nullable=False, default=TimeInForce.GTC)

    # Broker details
    broker_order_id = Column(String(100), nullable=True, index=True)
    broker = Column(String(50), nullable=False)

    # Metadata
    strategy_id = Column(String(36), nullable=True)
    commission = Column(Float, nullable=True, default=0.0)
    slippage = Column(Float, nullable=True, default=0.0)

    # Timestamps
    submitted_at = Column(DateTime, nullable=True)
    filled_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="orders")
    position = relationship("Position", back_populates="orders")

    # Indexes
    __table_args__ = (
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_broker_order', 'broker', 'broker_order_id'),
    )

    def is_complete(self) -> bool:
        """
        Check if order is in a terminal state.

        Returns:
            True if order cannot change anymore
        """
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]

    def is_active(self) -> bool:
        """
        Check if order is still active (can be filled).

        Returns:
            True if order is active
        """
        return self.status in [
            OrderStatus.PENDING,
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]

    def remaining_quantity(self) -> float:
        """
        Calculate remaining quantity to be filled.

        Returns:
            Remaining quantity
        """
        return self.quantity - self.filled_quantity

    def fill_percentage(self) -> float:
        """
        Calculate fill percentage.

        Returns:
            Fill percentage (0-100)
        """
        if self.quantity == 0:
            return 0.0
        return (self.filled_quantity / self.quantity) * 100

    def calculate_total_cost(self) -> float:
        """
        Calculate total cost including commission and slippage.

        Returns:
            Total cost
        """
        if not self.avg_fill_price or not self.filled_quantity:
            return 0.0

        base_cost = self.avg_fill_price * self.filled_quantity
        total_cost = base_cost + (self.commission or 0.0) + (self.slippage or 0.0)
        return total_cost

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Order(id={self.id}, symbol={self.symbol}, "
            f"side={self.side}, type={self.order_type}, "
            f"status={self.status}, quantity={self.quantity})>"
        )
