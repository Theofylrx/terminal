"""Indicator models and enums."""

from enum import Enum
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class IndicatorType(str, Enum):
    """Technical indicator types."""

    # Trend Indicators
    SMA = "sma"
    EMA = "ema"
    MACD = "macd"
    ADX = "adx"

    # Momentum Indicators
    RSI = "rsi"
    STOCHASTIC = "stochastic"
    CCI = "cci"
    WILLIAMS_R = "williams_r"
    ROC = "roc"

    # Volatility Indicators
    BOLLINGER_BANDS = "bollinger_bands"
    ATR = "atr"
    KELTNER_CHANNELS = "keltner_channels"

    # Volume Indicators
    OBV = "obv"
    VWAP = "vwap"
    MFI = "mfi"


class IndicatorResult(BaseModel):
    """Result of indicator calculation."""

    indicator_type: IndicatorType
    symbol: str
    timeframe: str
    timestamp: datetime
    value: float
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MACDResult(BaseModel):
    """MACD indicator result."""

    macd_line: float
    signal_line: float
    histogram: float
    timestamp: datetime


class BollingerBandsResult(BaseModel):
    """Bollinger Bands indicator result."""

    upper_band: float
    middle_band: float
    lower_band: float
    bandwidth: float
    percent_b: float
    timestamp: datetime


class StochasticResult(BaseModel):
    """Stochastic oscillator result."""

    k_line: float
    d_line: float
    timestamp: datetime
