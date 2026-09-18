"""API request and response schemas."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    """Signal response schema."""

    id: str
    symbol: str
    timeframe: str
    signal_type: str
    status: str
    entry_price: float
    current_price: Optional[float]
    target_price: Optional[float]
    stop_loss: Optional[float]
    confidence: float
    strategy: Optional[str]
    description: Optional[str]
    generated_at: datetime
    expires_at: Optional[datetime]


class GenerateSignalRequest(BaseModel):
    """Request to generate signal for symbol."""

    symbol: str = Field(..., description="Trading symbol")
    timeframe: str = Field(default="1h", description="Timeframe for analysis")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    version: str = "1.0.0"


class IndicatorResponse(BaseModel):
    """Indicator values response."""

    symbol: str
    timeframe: str
    timestamp: datetime
    indicators: dict
