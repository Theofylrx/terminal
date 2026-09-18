"""
Base Model for all database entities
Provides common fields and methods
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.ext.declarative import declared_attr
from shared.database.connection import Base


class BaseModel(Base):
    """
    Abstract base model for all database models.
    Provides common fields and methods.
    """

    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        """Auto-generate table name from class name."""
        return cls.__name__.lower() + 's'

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        unique=True,
        nullable=False,
        comment="Unique identifier (UUID)"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Creation timestamp (UTC)"
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp (UTC)"
    )

    def to_dict(self) -> dict:
        """
        Convert model instance to dictionary.

        Returns:
            Dictionary representation of the model

        Example:
            user_dict = user.to_dict()
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"
