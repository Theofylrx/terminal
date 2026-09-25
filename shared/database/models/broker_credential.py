"""Broker Credential Model - User-Specific Broker Integration."""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Index, UniqueConstraint, ForeignKey
from enum import Enum
from datetime import datetime
from typing import Dict, Any

from .base_model import BaseModel


class BrokerType(str, Enum):
    """Supported broker types."""
    ALPACA = "alpaca"
    BINANCE = "binance"
    INTERACTIVE_BROKERS = "interactive_brokers"
    KRAKEN = "kraken"
    COINBASE = "coinbase"
    TD_AMERITRADE = "td_ameritrade"


class BrokerCredential(BaseModel):
    """
    User-specific broker credentials.

    CRITICAL SECURITY REQUIREMENTS:
    - Each user has their own broker API keys
    - Credentials are encrypted at rest
    - API keys NEVER shared between users
    - All queries MUST filter by user_id

    This enables multi-tenancy where:
    - User A uses Alpaca with their own API keys
    - User B uses Binance with their own API keys
    - User C uses Interactive Brokers with their own API keys
    """

    __tablename__ = "broker_credentials"

    # User ownership - CRITICAL for multi-user isolation
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Broker identification
    broker_name = Column(String(50), nullable=False)  # "alpaca", "binance", "interactive_brokers"
    account_name = Column(String(100), nullable=True)  # User's friendly name for this account

    # Encrypted credentials - MUST be encrypted before storage
    # These are encrypted using Fernet encryption (shared/utils/encryption.py)
    encrypted_api_key = Column(Text, nullable=False)  # ENCRYPTED API key
    encrypted_api_secret = Column(Text, nullable=False)  # ENCRYPTED API secret
    encrypted_passphrase = Column(Text, nullable=True)  # ENCRYPTED (some brokers need this)

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)  # Is this the active broker?
    is_paper_trading = Column(Boolean, default=True, nullable=False)  # Sandbox vs production
    is_verified = Column(Boolean, default=False, nullable=False)  # Has connection been tested?

    # Broker-specific configuration (stored as JSON)
    # Examples:
    # - Alpaca: {"base_url": "https://paper-api.alpaca.markets", "data_url": "..."}
    # - Binance: {"base_url": "https://testnet.binance.vision", "recv_window": 5000}
    # - IB: {"host": "127.0.0.1", "port": 7497, "client_id": 1}
    config = Column(JSON, nullable=True)

    # Connection metadata
    last_verified_at = Column(DateTime, nullable=True)  # Last successful connection test
    verification_error = Column(Text, nullable=True)  # Last error message if verification failed

    # Audit fields
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes and constraints - IMPORTANT: user_id must be first for query performance
    __table_args__ = (
        # Index for fetching user's credentials
        Index('idx_broker_cred_user_id', 'user_id'),
        Index('idx_broker_cred_user_broker', 'user_id', 'broker_name'),
        Index('idx_broker_cred_user_active', 'user_id', 'is_active'),

        # Ensure one active broker per user per broker type
        # (User can have multiple broker accounts, but only one active at a time per broker)
        UniqueConstraint('user_id', 'broker_name', 'account_name', name='uq_user_broker_account'),
    )

    def to_dict(self, include_secrets: bool = False) -> Dict[str, Any]:
        """
        Convert to dictionary.

        Args:
            include_secrets: If True, include encrypted credentials (only for internal use)
                           If False, exclude credentials (for API responses)

        Returns:
            Dictionary representation
        """
        result = {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "broker_name": self.broker_name,
            "account_name": self.account_name,
            "is_active": self.is_active,
            "is_paper_trading": self.is_paper_trading,
            "is_verified": self.is_verified,
            "config": self.config,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
            "verification_error": self.verification_error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # NEVER include encrypted credentials in API responses unless explicitly requested
        if include_secrets:
            result.update({
                "encrypted_api_key": self.encrypted_api_key,
                "encrypted_api_secret": self.encrypted_api_secret,
                "encrypted_passphrase": self.encrypted_passphrase,
            })

        return result

    def __repr__(self) -> str:
        """String representation (without secrets)."""
        return (
            f"<BrokerCredential(user_id={self.user_id}, broker={self.broker_name}, "
            f"account={self.account_name}, active={self.is_active})>"
        )
