"""
Executor Service Configuration
Environment-based settings for order execution, position sizing, and risk management
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Executor Service settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Terminal Trading System - Executor Service"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8007

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # RabbitMQ
    RABBITMQ_URL: str = "amqp://guest:guest@localhost:5672/"

    # Broker API Credentials - Alpaca
    ALPACA_API_KEY: str = ""
    ALPACA_API_SECRET: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"  # Paper trading by default
    ALPACA_DATA_URL: str = "https://data.alpaca.markets"

    # Broker API Credentials - Binance
    BINANCE_API_KEY: str = ""
    BINANCE_API_SECRET: str = ""
    BINANCE_BASE_URL: str = "https://testnet.binance.vision"  # Testnet by default
    BINANCE_WS_URL: str = "wss://testnet.binance.vision/ws"

    # Position Sizing
    DEFAULT_POSITION_SIZE_METHOD: str = "fixed_risk"  # Options: fixed_risk, fixed_amount, kelly_criterion
    DEFAULT_RISK_PER_TRADE_PERCENT: float = 1.0  # % of account to risk per trade
    MIN_POSITION_SIZE_USD: float = 10.0  # Minimum position size in USD
    MAX_POSITION_SIZE_USD: float = 100000.0  # Maximum position size in USD
    ATR_MULTIPLIER_STOP_LOSS: float = 2.0  # ATR multiplier for stop-loss calculation

    # Risk Management
    MAX_RISK_PER_TRADE_PERCENT: float = 5.0  # Maximum risk per single trade
    MAX_ACCOUNT_RISK_PERCENT: float = 20.0  # Maximum total risk across all positions
    MAX_POSITIONS_PER_SYMBOL: int = 1  # Max positions in same symbol
    MAX_TOTAL_POSITIONS: int = 10  # Max total open positions
    MAX_DAILY_LOSS_PERCENT: float = 5.0  # Daily loss limit
    MAX_DAILY_TRADES: int = 50  # Daily trade limit

    # Account Protection
    MIN_ACCOUNT_BALANCE: float = 1000.0  # Minimum account balance to trade
    EMERGENCY_SHUTDOWN_LOSS_PERCENT: float = 10.0  # Emergency shutdown threshold
    MARGIN_USAGE_LIMIT_PERCENT: float = 80.0  # Maximum margin usage

    # Order Execution
    DEFAULT_ORDER_TYPE: str = "market"  # Options: market, limit
    LIMIT_ORDER_OFFSET_PERCENT: float = 0.1  # % offset for limit orders
    ORDER_TIMEOUT_SECONDS: int = 30  # Timeout for order execution
    MAX_SLIPPAGE_PERCENT: float = 0.5  # Maximum allowed slippage
    RETRY_FAILED_ORDERS: bool = True
    MAX_ORDER_RETRIES: int = 3

    # Position Management
    ENABLE_TRAILING_STOP: bool = True
    TRAILING_STOP_ACTIVATION_PERCENT: float = 2.0  # Activate after X% profit
    TRAILING_STOP_DISTANCE_PERCENT: float = 1.0  # Trail by X%
    AUTO_CLOSE_EOD: bool = False  # Auto-close positions end of day

    # Service Integration URLs
    MARKET_DATA_SERVICE_URL: str = "http://localhost:8003"
    TRADING_SERVICE_URL: str = "http://localhost:8002"
    NOTIFICATION_SERVICE_URL: str = "http://localhost:8008"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/tmp/executor_service.log"

    # Monitoring
    ENABLE_PROMETHEUS_METRICS: bool = True
    METRICS_PORT: int = 9007

    # Feature Flags
    ENABLE_PAPER_TRADING: bool = True  # Safety: default to paper trading
    ENABLE_LIVE_TRADING: bool = False  # Requires explicit enable
    DRY_RUN_MODE: bool = False  # Log orders without execution

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
