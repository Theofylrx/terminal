"""Technical Analyst Service Configuration."""

from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Technical Analyst Service settings."""

    # Application
    SERVICE_NAME: str = "technical-analyst-service"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    REDIS_STREAM_MAXLEN: int = Field(default=10000, env="REDIS_STREAM_MAXLEN")

    # Analysis Settings
    DEFAULT_SYMBOLS: List[str] = Field(
        default=["AAPL", "BTCUSDT", "EUR_USD"],
        env="DEFAULT_SYMBOLS"
    )
    DEFAULT_TIMEFRAMES: List[str] = Field(
        default=["1m", "5m", "15m", "1h", "4h", "1d"],
        env="DEFAULT_TIMEFRAMES"
    )

    # Indicator Parameters
    RSI_PERIOD: int = Field(default=14, env="RSI_PERIOD")
    RSI_OVERBOUGHT: float = Field(default=70.0, env="RSI_OVERBOUGHT")
    RSI_OVERSOLD: float = Field(default=30.0, env="RSI_OVERSOLD")

    MACD_FAST: int = Field(default=12, env="MACD_FAST")
    MACD_SLOW: int = Field(default=26, env="MACD_SLOW")
    MACD_SIGNAL: int = Field(default=9, env="MACD_SIGNAL")

    BB_PERIOD: int = Field(default=20, env="BB_PERIOD")
    BB_STD_DEV: float = Field(default=2.0, env="BB_STD_DEV")

    ATR_PERIOD: int = Field(default=14, env="ATR_PERIOD")
    ADX_PERIOD: int = Field(default=14, env="ADX_PERIOD")

    # Signal Generation
    MIN_CONFIDENCE: float = Field(default=60.0, env="MIN_CONFIDENCE")
    SIGNAL_COOLDOWN_MINUTES: int = Field(default=15, env="SIGNAL_COOLDOWN_MINUTES")
    MAX_SIGNALS_PER_SYMBOL: int = Field(default=100, env="MAX_SIGNALS_PER_SYMBOL")

    # Pattern Detection
    ENABLE_PATTERN_DETECTION: bool = Field(default=True, env="ENABLE_PATTERN_DETECTION")
    PATTERN_LOOKBACK_PERIODS: int = Field(default=50, env="PATTERN_LOOKBACK_PERIODS")

    # Performance
    INDICATOR_BATCH_SIZE: int = Field(default=100, env="INDICATOR_BATCH_SIZE")
    CALCULATION_INTERVAL_SECONDS: int = Field(default=60, env="CALCULATION_INTERVAL_SECONDS")

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables


settings = Settings()
