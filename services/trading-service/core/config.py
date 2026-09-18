"""
Trading Service Configuration
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Trading service settings."""

    # Application
    APP_NAME: str = "Terminal Trading System - Trading Service"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
