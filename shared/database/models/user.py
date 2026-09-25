"""
User Model
Represents a user of the trading system
"""

from sqlalchemy import Column, String, Boolean, Float, DateTime
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class User(BaseModel):
    """
    User model representing a system user.

    Attributes:
        email: User email (unique)
        username: Username (unique)
        hashed_password: Bcrypt hashed password
        is_active: Whether user account is active
        is_verified: Whether email is verified
        is_superuser: Admin privileges
        first_name: User's first name
        last_name: User's last name
        initial_capital: Starting capital
        current_capital: Current capital
        last_login: Last login timestamp
    """

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Profile
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)

    # Capital tracking
    initial_capital = Column(Float, nullable=True)
    current_capital = Column(Float, nullable=True)

    # Activity
    last_login = Column(DateTime, nullable=True)

    # Relationships
    positions = relationship("Position", back_populates="user", lazy="dynamic")
    orders = relationship("Order", back_populates="user", lazy="dynamic")
    auto_trading_configs = relationship("AutoTradingConfig", back_populates="user", lazy="dynamic")
    auto_trading_sessions = relationship("AutoTradingSession", back_populates="user", lazy="dynamic")

    def full_name(self) -> str:
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
