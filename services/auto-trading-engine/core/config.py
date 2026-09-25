"""
Auto-Trading Engine Configuration
Environment-based settings for autonomous trading
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Auto-Trading Engine settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Terminal Trading System - Auto-Trading Engine"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8005

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Service URLs (for calling other agents)
    MARKET_DATA_SERVICE_URL: str = "http://localhost:8003"
    TECHNICAL_ANALYST_SERVICE_URL: str = "http://localhost:8004"
    FUNDAMENTAL_ANALYST_SERVICE_URL: str = "http://localhost:8006"
    EXECUTOR_SERVICE_URL: str = "http://localhost:8007"
    TRADING_SERVICE_URL: str = "http://localhost:8002"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8008"

    # Worker Settings
    SYMBOL_MONITOR_INTERVAL_SECONDS: int = 5  # Check symbols every 5 seconds
    POSITION_MONITOR_INTERVAL_SECONDS: int = 5  # Check positions every 5 seconds
    SESSION_MANAGER_INTERVAL_SECONDS: int = 60  # Update sessions every minute

    # Auto-Trading Defaults
    DEFAULT_RISK_PER_TRADE_PERCENT: float = 1.0
    DEFAULT_MAX_CONCURRENT_POSITIONS: int = 3
    DEFAULT_MAX_DAILY_LOSS_PERCENT: float = 5.0
    DEFAULT_STOP_LOSS_PERCENT: float = 2.0
    DEFAULT_ENTRY_CONFIDENCE_THRESHOLD: float = 70.0
    DEFAULT_TRAILING_STOP_PERCENT: float = 2.0

    # Risk Limits (Safety)
    MAX_RISK_PER_TRADE_PERCENT: float = 5.0  # Absolute maximum
    MAX_CONCURRENT_POSITIONS_LIMIT: int = 10
    MAX_DAILY_LOSS_PERCENT_LIMIT: float = 15.0

    # Fundamental Analysis
    FUNDAMENTAL_FILTER_ENABLED_BY_DEFAULT: bool = True
    MIN_FUNDAMENTAL_SCORE: float = 50.0
    EARNINGS_BLACKOUT_DAYS: int = 3
    MIN_SENTIMENT_SCORE: float = -0.7

    # Confidence Boosting
    FUNDAMENTAL_SCORE_HIGH_BOOST: float = 5.0  # Score >= 80
    FUNDAMENTAL_SCORE_MED_BOOST: float = 3.0   # Score >= 70
    ANALYST_STRONG_BUY_BOOST: float = 3.0
    ANALYST_BUY_BOOST: float = 2.0
    SENTIMENT_HIGH_BOOST: float = 2.0  # Sentiment >= 0.5
    SENTIMENT_MED_BOOST: float = 1.0   # Sentiment >= 0.3
    REVENUE_GROWTH_BOOST: float = 2.0  # Growth >= 20%
    EARNINGS_SOON_PENALTY: float = -5.0  # Within 3 days
    EARNINGS_APPROACHING_PENALTY: float = -3.0  # Within 7 days
    NEGATIVE_SENTIMENT_PENALTY: float = -3.0  # < -0.3
    HIGH_DEBT_PENALTY: float = -2.0  # Debt/Equity > 2.5

    # Emergency Shutdown
    EMERGENCY_SHUTDOWN_ENABLED: bool = True
    AUTO_PAUSE_ON_DAILY_LOSS: bool = True
    CIRCUIT_BREAKER_THRESHOLD: float = 10.0  # % account drawdown

    # Logging
    LOG_LEVEL: str = "INFO"

    # Monitoring
    ENABLE_PROMETHEUS_METRICS: bool = True
    METRICS_PORT: int = 9005

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
