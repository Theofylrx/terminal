"""Pattern detection models and enums."""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class PatternType(str, Enum):
    """Chart and candlestick pattern types."""

    # Candlestick Patterns
    DOJI = "doji"
    HAMMER = "hammer"
    INVERTED_HAMMER = "inverted_hammer"
    HANGING_MAN = "hanging_man"
    SHOOTING_STAR = "shooting_star"
    BULLISH_ENGULFING = "bullish_engulfing"
    BEARISH_ENGULFING = "bearish_engulfing"
    MORNING_STAR = "morning_star"
    EVENING_STAR = "evening_star"

    # Chart Patterns
    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    TRIPLE_TOP = "triple_top"
    TRIPLE_BOTTOM = "triple_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"


class PatternSignal(str, Enum):
    """Pattern signal direction."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class PatternResult(BaseModel):
    """Result of pattern detection."""

    pattern_type: PatternType
    signal: PatternSignal
    symbol: str
    timeframe: str
    timestamp: datetime
    confidence: float = Field(..., ge=0, le=100, description="Confidence score 0-100")
    description: str = Field(..., description="Pattern description")

    # Price levels
    entry_price: Optional[float] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
