"""
Executor Service API Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order side enum."""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Order type enum."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "STOP_LOSS"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


class AssetClass(str, Enum):
    """Asset class enum."""
    STOCK = "STOCK"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"


class PositionSizeMethod(str, Enum):
    """Position sizing method."""
    FIXED_RISK = "fixed_risk"  # Risk % of account
    FIXED_AMOUNT = "fixed_amount"  # Fixed dollar amount
    KELLY_CRITERION = "kelly_criterion"  # Kelly formula


# ==================== Order Execution ====================

class ExecuteOrderRequest(BaseModel):
    """Request to execute a trade order."""

    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol (e.g., BTCUSDT, AAPL)")
    asset_class: AssetClass = Field(..., description="Asset type")
    side: OrderSide = Field(..., description="BUY or SELL")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")

    quantity: float = Field(..., gt=0, description="Quantity to trade")
    limit_price: Optional[float] = Field(None, gt=0, description="Limit price (for LIMIT orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for STOP orders)")

    stop_loss_price: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit_price: Optional[float] = Field(None, gt=0, description="Take profit price")

    strategy_id: Optional[str] = Field(None, description="Strategy that triggered this order")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('limit_price')
    def validate_limit_price(cls, v, values):
        """Validate limit price for LIMIT orders."""
        if values.get('order_type') == OrderType.LIMIT and not v:
            raise ValueError("limit_price required for LIMIT orders")
        return v

    @validator('stop_price')
    def validate_stop_price(cls, v, values):
        """Validate stop price for STOP orders."""
        if values.get('order_type') in [OrderType.STOP_LOSS, OrderType.STOP_LIMIT] and not v:
            raise ValueError("stop_price required for STOP orders")
        return v


class ExecuteOrderResponse(BaseModel):
    """Response after executing an order."""

    success: bool = Field(..., description="Whether order was successfully executed")
    order_id: Optional[str] = Field(None, description="Internal order ID")
    broker_order_id: Optional[str] = Field(None, description="Broker order ID")

    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., description="Quantity ordered")

    status: str = Field(..., description="Order status")
    filled_quantity: float = Field(default=0.0, description="Quantity filled")
    avg_fill_price: Optional[float] = Field(None, description="Average fill price")

    commission: Optional[float] = Field(None, description="Trading commission")
    slippage: Optional[float] = Field(None, description="Price slippage")

    error_message: Optional[str] = Field(None, description="Error message if failed")
    submitted_at: Optional[datetime] = Field(None, description="Submission timestamp")
    filled_at: Optional[datetime] = Field(None, description="Fill timestamp")


# ==================== Position Sizing ====================

class PositionSizeRequest(BaseModel):
    """Request to calculate position size."""

    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    entry_price: float = Field(..., gt=0, description="Expected entry price")
    stop_loss_price: float = Field(..., gt=0, description="Stop loss price")

    risk_per_trade_percent: Optional[float] = Field(1.0, gt=0, le=100, description="Risk % of account")
    method: PositionSizeMethod = Field(PositionSizeMethod.FIXED_RISK, description="Sizing method")
    risk_multiplier: Optional[float] = Field(1.0, gt=0, le=5, description="Risk multiplier (from strategy)")

    account_balance: Optional[float] = Field(None, gt=0, description="Account balance (if not auto-fetched)")


class PositionSizeResponse(BaseModel):
    """Response with calculated position size."""

    success: bool = Field(..., description="Whether calculation succeeded")
    quantity: float = Field(..., description="Recommended quantity to trade")
    position_value: float = Field(..., description="Position value in USD")
    risk_amount: float = Field(..., description="Amount at risk (USD)")
    risk_percent: float = Field(..., description="Risk as % of account")

    account_balance: float = Field(..., description="Account balance used")
    entry_price: float = Field(..., description="Entry price")
    stop_loss_price: float = Field(..., description="Stop loss price")
    stop_loss_distance: float = Field(..., description="Distance to stop loss (%)")

    error_message: Optional[str] = Field(None, description="Error message if failed")


# ==================== Risk Management ====================

class RiskCheckRequest(BaseModel):
    """Request to validate risk before executing order."""

    user_id: str = Field(..., description="User ID")
    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    quantity: float = Field(..., gt=0, description="Quantity to trade")
    entry_price: float = Field(..., gt=0, description="Expected entry price")

    stop_loss_price: Optional[float] = Field(None, gt=0, description="Stop loss price")
    position_value: Optional[float] = Field(None, description="Position value (auto-calculated if None)")


class RiskCheckResponse(BaseModel):
    """Response with risk validation results."""

    approved: bool = Field(..., description="Whether risk check passed")
    risk_score: float = Field(..., description="Risk score (0-100, lower is safer)")

    # Risk metrics
    position_risk_percent: float = Field(..., description="Risk % for this position")
    total_account_risk_percent: float = Field(..., description="Total account risk %")
    margin_usage_percent: float = Field(..., description="Margin usage %")

    # Position limits
    positions_count: int = Field(..., description="Current open positions")
    max_positions_allowed: int = Field(..., description="Maximum positions allowed")
    positions_in_symbol: int = Field(..., description="Positions in same symbol")

    # Violations
    violations: list[str] = Field(default_factory=list, description="List of violations")
    warnings: list[str] = Field(default_factory=list, description="List of warnings")

    error_message: Optional[str] = Field(None, description="Error message if check failed")


# ==================== Order Status ====================

class OrderStatus(BaseModel):
    """Order status response."""

    order_id: str = Field(..., description="Internal order ID")
    broker_order_id: Optional[str] = Field(None, description="Broker order ID")

    symbol: str = Field(..., description="Trading symbol")
    side: OrderSide = Field(..., description="BUY or SELL")
    order_type: OrderType = Field(..., description="Order type")

    quantity: float = Field(..., description="Total quantity")
    filled_quantity: float = Field(..., description="Filled quantity")
    remaining_quantity: float = Field(..., description="Remaining quantity")

    status: str = Field(..., description="Order status")
    avg_fill_price: Optional[float] = Field(None, description="Average fill price")

    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    filled_at: Optional[datetime] = Field(None, description="Fill timestamp")


# ==================== Positions & Account ====================

class PositionResponse(BaseModel):
    """Single position response."""

    symbol: str = Field(..., description="Trading symbol")
    quantity: float = Field(..., description="Position quantity")
    avg_entry_price: float = Field(..., description="Average entry price")
    current_price: float = Field(..., description="Current market price")
    market_value: float = Field(..., description="Current market value")
    cost_basis: float = Field(..., description="Total cost basis")
    unrealized_pnl: float = Field(..., description="Unrealized P&L")
    unrealized_pnl_percent: float = Field(..., description="Unrealized P&L percentage")
    side: str = Field(..., description="Position side (long/short)")
    broker: str = Field(..., description="Broker name (alpaca/binance)")


class PositionsResponse(BaseModel):
    """All positions response."""

    success: bool = Field(..., description="Whether request succeeded")
    positions: list[PositionResponse] = Field(default_factory=list, description="List of positions")
    total_value: float = Field(default=0.0, description="Total portfolio value")
    total_pnl: float = Field(default=0.0, description="Total unrealized P&L")
    total_pnl_percent: float = Field(default=0.0, description="Total unrealized P&L percentage")
    count: int = Field(default=0, description="Number of positions")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class AccountResponse(BaseModel):
    """Account information response."""

    success: bool = Field(..., description="Whether request succeeded")
    user_id: str = Field(..., description="User ID")

    # Alpaca account data
    alpaca_cash: float = Field(default=0.0, description="Alpaca cash balance")
    alpaca_equity: float = Field(default=0.0, description="Alpaca total equity")
    alpaca_buying_power: float = Field(default=0.0, description="Alpaca buying power")

    # Binance account data
    binance_usdt_balance: float = Field(default=0.0, description="Binance USDT balance")
    binance_total_value: float = Field(default=0.0, description="Binance total portfolio value (USDT)")

    # Combined data
    total_cash: float = Field(default=0.0, description="Total cash across all brokers")
    total_equity: float = Field(default=0.0, description="Total equity across all brokers")

    error_message: Optional[str] = Field(None, description="Error message if failed")


class ClosePositionResponse(BaseModel):
    """Response after closing a position."""

    success: bool = Field(..., description="Whether position was closed successfully")
    symbol: str = Field(..., description="Symbol that was closed")
    broker: str = Field(..., description="Broker name")
    order_id: Optional[str] = Field(None, description="Close order ID")
    message: str = Field(..., description="Result message")
    error_message: Optional[str] = Field(None, description="Error message if failed")


# ==================== Health Check ====================

class HealthResponse(BaseModel):
    """Service health check response."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(..., description="Current timestamp")

    # Additional health metrics
    database_connected: bool = Field(..., description="Database connection status")
    alpaca_connected: bool = Field(..., description="Alpaca API status")
    binance_connected: bool = Field(..., description="Binance API status")
