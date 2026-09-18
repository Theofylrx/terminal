"""
Trading Schemas
Pydantic models for request/response validation
"""

from typing import Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


# Enums
class PositionSideEnum(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class AssetClassEnum(str, Enum):
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"


class OrderSideEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderTypeEnum(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForceEnum(str, Enum):
    GTC = "GTC"
    DAY = "DAY"
    IOC = "IOC"


# Position Schemas
class CreatePositionRequest(BaseModel):
    """Create position request."""
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT)")
    asset_class: AssetClassEnum = Field(..., description="Asset class")
    side: PositionSideEnum = Field(..., description="Position direction")
    quantity: float = Field(..., gt=0, description="Position size")
    entry_price: float = Field(..., gt=0, description="Entry price")
    broker: str = Field(..., description="Broker name")
    strategy_id: Optional[str] = Field(None, description="Strategy ID")
    stop_loss_price: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit_price: Optional[float] = Field(None, gt=0, description="Take profit price")


class PositionResponse(BaseModel):
    """Position response."""
    id: str
    user_id: str
    symbol: str
    asset_class: str
    side: str
    status: str
    quantity: float
    avg_entry_price: float
    current_price: Optional[float] = None
    market_value: Optional[float] = None
    cost_basis: float
    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    stop_loss_price: Optional[float] = None
    take_profit_price: Optional[float] = None
    broker: str
    strategy_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UpdatePositionPriceRequest(BaseModel):
    """Update position price request."""
    current_price: float = Field(..., gt=0, description="Current market price")


class ClosePositionRequest(BaseModel):
    """Close position request."""
    close_price: float = Field(..., gt=0, description="Closing price")


# Order Schemas
class CreateOrderRequest(BaseModel):
    """Create order request."""
    symbol: str = Field(..., description="Trading symbol")
    asset_class: AssetClassEnum = Field(..., description="Asset class")
    order_type: OrderTypeEnum = Field(..., description="Order type")
    side: OrderSideEnum = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Order quantity")
    broker: str = Field(..., description="Broker name")
    limit_price: Optional[float] = Field(None, gt=0, description="Limit price (for LIMIT orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for STOP orders)")
    time_in_force: TimeInForceEnum = Field(TimeInForceEnum.GTC, description="Time in force")
    position_id: Optional[str] = Field(None, description="Associated position ID")
    strategy_id: Optional[str] = Field(None, description="Strategy ID")


class OrderResponse(BaseModel):
    """Order response."""
    id: str
    user_id: str
    position_id: Optional[str] = None
    symbol: str
    asset_class: str
    order_type: str
    side: str
    status: str
    quantity: float
    filled_quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    avg_fill_price: Optional[float] = None
    time_in_force: str
    broker_order_id: Optional[str] = None
    broker: str
    strategy_id: Optional[str] = None
    commission: Optional[float] = None
    slippage: Optional[float] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Portfolio Schemas
class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary response."""
    total_value: float = Field(..., description="Total market value of all positions")
    total_cost: float = Field(..., description="Total cost basis")
    total_unrealized_pnl: float = Field(..., description="Total unrealized P&L")
    total_pnl_percentage: float = Field(..., description="P&L percentage")
    position_count: int = Field(..., description="Number of open positions")
    by_asset_class: dict = Field(..., description="Breakdown by asset class")
    positions: list = Field(..., description="List of positions")


class MessageResponse(BaseModel):
    """Generic message response."""
    message: str
    detail: Optional[str] = None
