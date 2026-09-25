"""
Auto-Trading Configuration Model
Represents user configuration for autonomous trading on specific symbols
"""

from sqlalchemy import Column, String, Boolean, Float, Integer, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from .base_model import BaseModel


class StrategyType(str, enum.Enum):
    """Strategy type for auto-trading."""
    AGGRESSIVE = "AGGRESSIVE"
    BALANCED = "BALANCED"
    CONSERVATIVE = "CONSERVATIVE"


class AutoTradingConfig(BaseModel):
    """
    Auto-Trading Configuration model.

    Defines how the system should autonomously trade a specific symbol for a user.

    Attributes:
        user_id: User who owns this configuration
        symbol: Trading symbol (e.g., "AAPL", "BTCUSDT")
        enabled: Whether auto-trading is currently enabled

        # Risk Parameters
        risk_per_trade_percent: Percentage of capital to risk per trade (e.g., 1.0 = 1%)
        max_concurrent_positions: Maximum number of open positions for this symbol
        max_daily_loss_percent: Maximum daily loss allowed before shutdown (e.g., 5.0 = 5%)
        stop_loss_percent: Stop loss percentage from entry (e.g., 2.0 = 2%)

        # Strategy Settings
        strategy_type: Trading strategy (AGGRESSIVE, BALANCED, CONSERVATIVE)
        entry_confidence_threshold: Minimum signal confidence to enter (e.g., 70.0 = 70%)

        # Trading Hours
        trading_start_hour: Hour when trading can start (0-23, UTC)
        trading_end_hour: Hour when trading must stop (0-23, UTC)

        # Auto-Management Settings
        auto_close_on_correction: Auto-close profitable positions if correction detected
        trailing_stop_enabled: Enable trailing stop-loss
        trailing_stop_percent: Trailing stop percentage (e.g., 2.0 = 2%)

        # Metadata
        broker: Broker to use for this symbol
        asset_class: Asset type (STOCK, CRYPTO, FOREX)
    """

    __tablename__ = "auto_trading_configs"

    # Ownership
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Symbol & Status
    symbol = Column(String(20), nullable=False, index=True)
    enabled = Column(Boolean, default=False, nullable=False, index=True)

    # Risk Parameters
    risk_per_trade_percent = Column(Float, default=1.0, nullable=False)
    max_concurrent_positions = Column(Integer, default=3, nullable=False)
    max_daily_loss_percent = Column(Float, default=5.0, nullable=False)
    stop_loss_percent = Column(Float, default=2.0, nullable=False)

    # Strategy Settings
    strategy_type = Column(
        SQLEnum(StrategyType, name="strategy_type"),
        default=StrategyType.BALANCED,
        nullable=False
    )
    entry_confidence_threshold = Column(Float, default=70.0, nullable=False)

    # Trading Hours (UTC)
    trading_start_hour = Column(Integer, default=0, nullable=False)
    trading_end_hour = Column(Integer, default=23, nullable=False)

    # Auto-Management Settings
    auto_close_on_correction = Column(Boolean, default=True, nullable=False)
    trailing_stop_enabled = Column(Boolean, default=True, nullable=False)
    trailing_stop_percent = Column(Float, default=2.0, nullable=False)

    # Metadata
    broker = Column(String(50), nullable=False)
    asset_class = Column(String(20), nullable=False)

    # Relationships
    user = relationship("User", back_populates="auto_trading_configs")
    sessions = relationship("AutoTradingSession", back_populates="config")

    # Indexes
    __table_args__ = (
        Index('idx_user_symbol_unique', 'user_id', 'symbol', unique=True),
        Index('idx_enabled_symbols', 'enabled', 'symbol'),
    )

    def is_within_trading_hours(self, current_hour: int) -> bool:
        """
        Check if current time is within configured trading hours.

        Args:
            current_hour: Current hour (0-23, UTC)

        Returns:
            True if within trading hours, False otherwise
        """
        return self.trading_start_hour <= current_hour <= self.trading_end_hour

    def calculate_position_size(self, capital: float, entry_price: float) -> dict:
        """
        Calculate position size based on risk parameters.

        Args:
            capital: Available capital
            entry_price: Entry price for the trade

        Returns:
            Dictionary with position_size, quantity, risk_amount

        Example:
            config.calculate_position_size(capital=10000, entry_price=150)
            # Returns: {
            #   'position_value': 5000,
            #   'quantity': 33.33,
            #   'risk_amount': 100
            # }
        """
        risk_amount = capital * (self.risk_per_trade_percent / 100)
        stop_loss_fraction = self.stop_loss_percent / 100

        # Position size = Risk Amount / Stop Loss Percentage
        position_value = risk_amount / stop_loss_fraction

        # Limit to 50% of capital max
        max_position_value = capital * 0.5
        position_value = min(position_value, max_position_value)

        quantity = position_value / entry_price

        return {
            'position_value': position_value,
            'quantity': quantity,
            'risk_amount': risk_amount
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AutoTradingConfig(id={self.id}, user_id={self.user_id}, "
            f"symbol={self.symbol}, enabled={self.enabled})>"
        )
