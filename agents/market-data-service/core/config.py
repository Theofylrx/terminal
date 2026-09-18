"""Market Data Service Configuration."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Market Data Service settings."""

    # Application
    SERVICE_NAME: str = "market-data-service"
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

    # Alpaca (Stocks)
    ALPACA_API_KEY: Optional[str] = Field(default=None, env="ALPACA_API_KEY")
    ALPACA_API_SECRET: Optional[str] = Field(default=None, env="ALPACA_API_SECRET")
    ALPACA_BASE_URL: str = Field(default="https://paper-api.alpaca.markets", env="ALPACA_BASE_URL")
    ALPACA_DATA_URL: str = Field(default="https://data.alpaca.markets", env="ALPACA_DATA_URL")
    ALPACA_WS_URL: str = Field(default="wss://stream.data.alpaca.markets/v2/iex", env="ALPACA_WS_URL")

    # Binance (Crypto)
    BINANCE_API_KEY: Optional[str] = Field(default=None, env="BINANCE_API_KEY")
    BINANCE_API_SECRET: Optional[str] = Field(default=None, env="BINANCE_API_SECRET")
    BINANCE_BASE_URL: str = Field(default="https://api.binance.com", env="BINANCE_BASE_URL")
    BINANCE_WS_URL: str = Field(default="wss://stream.binance.com:9443", env="BINANCE_WS_URL")
    BINANCE_TESTNET: bool = Field(default=True, env="BINANCE_TESTNET")

    # OANDA (Forex)
    OANDA_API_KEY: Optional[str] = Field(default=None, env="OANDA_API_KEY")
    OANDA_ACCOUNT_ID: Optional[str] = Field(default=None, env="OANDA_ACCOUNT_ID")
    OANDA_BASE_URL: str = Field(default="https://api-fxpractice.oanda.com", env="OANDA_BASE_URL")
    OANDA_STREAM_URL: str = Field(default="https://stream-fxpractice.oanda.com", env="OANDA_STREAM_URL")

    # WebSocket Server
    WS_HOST: str = Field(default="0.0.0.0", env="WS_HOST")
    WS_PORT: int = Field(default=8001, env="WS_PORT")
    WS_MAX_CONNECTIONS: int = Field(default=1000, env="WS_MAX_CONNECTIONS")
    WS_PING_INTERVAL: int = Field(default=30, env="WS_PING_INTERVAL")
    WS_PING_TIMEOUT: int = Field(default=10, env="WS_PING_TIMEOUT")

    # Data Collection
    ENABLE_ALPACA: bool = Field(default=False, env="ENABLE_ALPACA")
    ENABLE_BINANCE: bool = Field(default=False, env="ENABLE_BINANCE")
    ENABLE_OANDA: bool = Field(default=False, env="ENABLE_OANDA")

    # Default symbols to subscribe
    DEFAULT_STOCK_SYMBOLS: List[str] = Field(
        default=["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
        env="DEFAULT_STOCK_SYMBOLS"
    )
    DEFAULT_CRYPTO_SYMBOLS: List[str] = Field(
        default=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT"],
        env="DEFAULT_CRYPTO_SYMBOLS"
    )
    DEFAULT_FOREX_SYMBOLS: List[str] = Field(
        default=["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CAD"],
        env="DEFAULT_FOREX_SYMBOLS"
    )

    # Reconnection settings
    RECONNECT_MAX_ATTEMPTS: int = Field(default=10, env="RECONNECT_MAX_ATTEMPTS")
    RECONNECT_BASE_DELAY: float = Field(default=1.0, env="RECONNECT_BASE_DELAY")
    RECONNECT_MAX_DELAY: float = Field(default=60.0, env="RECONNECT_MAX_DELAY")

    # Data retention
    OHLCV_RETENTION_DAYS: int = Field(default=365, env="OHLCV_RETENTION_DAYS")
    QUOTE_RETENTION_DAYS: int = Field(default=7, env="QUOTE_RETENTION_DAYS")
    TRADE_RETENTION_DAYS: int = Field(default=30, env="TRADE_RETENTION_DAYS")

    # Performance
    BATCH_SIZE: int = Field(default=100, env="BATCH_SIZE")
    FLUSH_INTERVAL_SECONDS: int = Field(default=5, env="FLUSH_INTERVAL_SECONDS")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
