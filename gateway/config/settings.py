"""
API Gateway Configuration
Environment-based settings for the gateway
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Gateway settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Terminal Trading System - API Gateway"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080

    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_ENABLED: bool = True

    # Database (for gateway session management)
    DATABASE_URL: str

    # Redis (for rate limiting and caching)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Service URLs (internal microservices)
    AUTH_SERVICE_URL: str = "http://auth-service:8000"
    TRADING_SERVICE_URL: str = "http://trading-service:8000"
    ANALYTICS_SERVICE_URL: str = "http://analytics-service:8000"
    STRATEGY_SERVICE_URL: str = "http://strategy-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8000"

    # Timeouts
    SERVICE_TIMEOUT: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 5  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
