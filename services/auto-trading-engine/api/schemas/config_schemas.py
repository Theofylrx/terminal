"""
Pydantic schemas for Auto-Trading Configuration API
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AutoTradingConfigCreate(BaseModel):
    """Schema for creating auto-trading configuration."""

    symbol: str = Field(..., description="Trading symbol (e.g., AAPL, BTCUSDT)")
    broker: str = Field(..., description="Broker to use (e.g., ALPACA, BINANCE)")
    asset_class: str = Field(..., description="Asset class (STOCK, CRYPTO, FOREX)")

    # Risk Parameters
    risk_per_trade_percent: float = Field(default=1.0, ge=0.1, le=5.0)
    max_concurrent_positions: int = Field(default=3, ge=1, le=10)
    max_daily_loss_percent: float = Field(default=5.0, ge=1.0, le=15.0)
    stop_loss_percent: float = Field(default=2.0, ge=0.5, le=10.0)

    # Strategy Settings
    strategy_type: str = Field(default="BALANCED", pattern="^(AGGRESSIVE|BALANCED|CONSERVATIVE)$")
    entry_confidence_threshold: float = Field(default=70.0, ge=50.0, le=95.0)

    # Trading Hours (UTC)
    trading_start_hour: int = Field(default=0, ge=0, le=23)
    trading_end_hour: int = Field(default=23, ge=0, le=23)

    # Auto-Management Settings
    auto_close_on_correction: bool = Field(default=True)
    trailing_stop_enabled: bool = Field(default=True)
    trailing_stop_percent: float = Field(default=2.0, ge=0.5, le=5.0)


class AutoTradingConfigUpdate(BaseModel):
    """Schema for updating auto-trading configuration."""

    risk_per_trade_percent: Optional[float] = Field(None, ge=0.1, le=5.0)
    max_concurrent_positions: Optional[int] = Field(None, ge=1, le=10)
    max_daily_loss_percent: Optional[float] = Field(None, ge=1.0, le=15.0)
    stop_loss_percent: Optional[float] = Field(None, ge=0.5, le=10.0)
    strategy_type: Optional[str] = Field(None, pattern="^(AGGRESSIVE|BALANCED|CONSERVATIVE)$")
    entry_confidence_threshold: Optional[float] = Field(None, ge=50.0, le=95.0)
    trading_start_hour: Optional[int] = Field(None, ge=0, le=23)
    trading_end_hour: Optional[int] = Field(None, ge=0, le=23)
    auto_close_on_correction: Optional[bool] = None
    trailing_stop_enabled: Optional[bool] = None
    trailing_stop_percent: Optional[float] = Field(None, ge=0.5, le=5.0)


class AutoTradingConfigResponse(BaseModel):
    """Schema for auto-trading configuration response."""

    id: str
    user_id: str
    symbol: str
    enabled: bool
    broker: str
    asset_class: str

    # Risk Parameters
    risk_per_trade_percent: float
    max_concurrent_positions: int
    max_daily_loss_percent: float
    stop_loss_percent: float

    # Strategy Settings
    strategy_type: str
    entry_confidence_threshold: float

    # Trading Hours
    trading_start_hour: int
    trading_end_hour: int

    # Auto-Management Settings
    auto_close_on_correction: bool
    trailing_stop_enabled: bool
    trailing_stop_percent: float

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionStatsResponse(BaseModel):
    """Schema for session statistics response."""

    id: str
    symbol: str
    status: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    best_trade_pnl: float
    worst_trade_pnl: float
    current_open_positions: int
    daily_loss: float
    started_at: datetime
    last_activity_at: Optional[datetime]

    class Config:
        from_attributes = True
