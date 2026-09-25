"""
Auto-Trading Session Model
Represents an active auto-trading session for a symbol
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Index, Enum as SQLEnum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base_model import BaseModel


class SessionStatus(str, enum.Enum):
    """Auto-trading session status."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


class AutoTradingSession(BaseModel):
    """
    Auto-Trading Session model.

    Tracks an active auto-trading session for a specific symbol and user.

    Attributes:
        config_id: Reference to auto_trading_config
        user_id: User who owns this session
        symbol: Trading symbol
        status: Session status (ACTIVE, PAUSED, STOPPED, ERROR)

        # Session Statistics
        total_trades: Total number of trades executed
        winning_trades: Number of profitable trades
        losing_trades: Number of losing trades
        total_pnl: Total profit/loss for this session
        best_trade_pnl: Largest winning trade
        worst_trade_pnl: Largest losing trade

        # Risk Tracking
        current_open_positions: Number of currently open positions
        daily_loss: Loss accumulated today
        last_trade_at: Timestamp of last trade

        # Session Timing
        started_at: When session started
        last_activity_at: Last time system took action
        stopped_at: When session stopped (if stopped)

        # Error Tracking
        error_count: Number of errors encountered
        last_error_message: Last error that occurred
    """

    __tablename__ = "auto_trading_sessions"

    # References
    config_id = Column(String(36), ForeignKey("auto_trading_configs.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    # Session Details
    symbol = Column(String(20), nullable=False, index=True)
    status = Column(
        SQLEnum(SessionStatus, name="session_status"),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True
    )

    # Session Statistics
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    total_pnl = Column(Float, default=0.0, nullable=False)
    best_trade_pnl = Column(Float, default=0.0, nullable=False)
    worst_trade_pnl = Column(Float, default=0.0, nullable=False)

    # Risk Tracking
    current_open_positions = Column(Integer, default=0, nullable=False)
    daily_loss = Column(Float, default=0.0, nullable=False)
    last_trade_at = Column(DateTime, nullable=True)

    # Session Timing
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    stopped_at = Column(DateTime, nullable=True)

    # Error Tracking
    error_count = Column(Integer, default=0, nullable=False)
    last_error_message = Column(String(500), nullable=True)

    # Relationships
    config = relationship("AutoTradingConfig", back_populates="sessions")
    user = relationship("User", back_populates="auto_trading_sessions")

    # Indexes
    __table_args__ = (
        Index('idx_user_symbol_status', 'user_id', 'symbol', 'status'),
        Index('idx_active_sessions', 'status', 'last_activity_at'),
    )

    def calculate_win_rate(self) -> float:
        """
        Calculate win rate percentage.

        Returns:
            Win rate as percentage (0-100)
        """
        if self.total_trades == 0:
            return 0.0

        return (self.winning_trades / self.total_trades) * 100

    def record_trade(self, pnl: float) -> None:
        """
        Record a trade result and update statistics.

        Args:
            pnl: Profit/loss of the trade
        """
        self.total_trades += 1
        self.total_pnl += pnl
        self.last_trade_at = datetime.utcnow()
        self.last_activity_at = datetime.utcnow()

        if pnl > 0:
            self.winning_trades += 1
            if pnl > self.best_trade_pnl:
                self.best_trade_pnl = pnl
        else:
            self.losing_trades += 1
            if pnl < self.worst_trade_pnl:
                self.worst_trade_pnl = pnl

            # Track daily loss
            self.daily_loss += abs(pnl)

    def record_error(self, error_message: str) -> None:
        """
        Record an error occurrence.

        Args:
            error_message: Error description
        """
        self.error_count += 1
        self.last_error_message = error_message[:500]  # Truncate to fit column
        self.last_activity_at = datetime.utcnow()

    def reset_daily_loss(self) -> None:
        """Reset daily loss counter (call at start of new trading day)."""
        self.daily_loss = 0.0

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<AutoTradingSession(id={self.id}, symbol={self.symbol}, "
            f"status={self.status}, total_trades={self.total_trades}, "
            f"win_rate={self.calculate_win_rate():.1f}%)>"
        )
