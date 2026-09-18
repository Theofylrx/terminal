"""API request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ========== Request Schemas ==========

class SubscribeRequest(BaseModel):
    """Request to subscribe to symbols."""

    broker: str = Field(..., description="Broker name (alpaca, binance, oanda)")
    symbols: List[str] = Field(..., description="List of symbols to subscribe to")


class UnsubscribeRequest(BaseModel):
    """Request to unsubscribe from symbols."""

    broker: str = Field(..., description="Broker name")
    symbols: List[str] = Field(..., description="List of symbols to unsubscribe from")


class HistoricalBarsRequest(BaseModel):
    """Request for historical bars."""

    broker: str = Field(..., description="Broker name")
    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(..., description="Bar timeframe (1m, 5m, 1h, etc.)")
    start: datetime = Field(..., description="Start datetime")
    end: datetime = Field(..., description="End datetime")
    limit: Optional[int] = Field(None, description="Max bars to return")


# ========== Response Schemas ==========

class BarResponse(BaseModel):
    """OHLCV bar response."""

    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: Optional[int] = None
    vwap: Optional[float] = None


class QuoteResponse(BaseModel):
    """Quote response."""

    symbol: str
    timestamp: datetime
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float
    spread: float
    mid_price: float


class TradeResponse(BaseModel):
    """Trade response."""

    symbol: str
    timestamp: datetime
    price: float
    size: float
    notional: float
    side: Optional[str] = None
    exchange: Optional[str] = None


class StatusResponse(BaseModel):
    """Service status response."""

    connectors: dict = Field(..., description="Connector connection status")
    subscriptions: dict = Field(..., description="Active subscriptions")
    websocket_clients: int = Field(..., description="Number of WebSocket clients")


class SubscriptionResponse(BaseModel):
    """Subscription response."""

    broker: str
    symbols: List[str]
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Current timestamp")
    version: str = Field(default="1.0.0", description="Service version")
