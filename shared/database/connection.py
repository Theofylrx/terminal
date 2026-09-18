"""
Database Connection Management
Provides async database session handling
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

# Base class for all models
Base = declarative_base()

# Global engine and session maker
_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker | None = None


def get_database_url() -> str:
    """
    Get database URL from environment variables.

    Returns:
        Database connection string

    Raises:
        ValueError: If DATABASE_URL not set
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    # Convert postgres:// to postgresql+asyncpg://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return db_url


def init_db(database_url: str | None = None, echo: bool = False) -> AsyncEngine:
    """
    Initialize database engine and session maker.

    Args:
        database_url: Database connection string (uses env var if None)
        echo: Whether to echo SQL queries (for debugging)

    Returns:
        Async database engine

    Example:
        engine = init_db()
    """
    global _engine, _async_session_maker

    if _engine is None:
        url = database_url or get_database_url()

        _engine = create_async_engine(
            url,
            echo=echo,
            future=True,
            pool_pre_ping=True,  # Verify connections before using
            pool_size=10,        # Connection pool size
            max_overflow=20,     # Additional connections if pool exhausted
            # Use NullPool for serverless environments
            # poolclass=NullPool if os.getenv("SERVERLESS") else None
        )

        _async_session_maker = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False
        )

    return _engine


def get_session_maker() -> async_sessionmaker:
    """
    Get async session maker.

    Returns:
        Async session maker

    Raises:
        RuntimeError: If database not initialized
    """
    global _async_session_maker

    if _async_session_maker is None:
        init_db()

    return _async_session_maker


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI to inject database session.

    Yields:
        Async database session

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            users = await user_repo.get_all()
            return users
    """
    session_maker = get_session_maker()

    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """
    Close database connections.
    Call this on application shutdown.

    Example:
        @app.on_event("shutdown")
        async def shutdown():
            await close_db()
    """
    global _engine

    if _engine:
        await _engine.dispose()
        _engine = None


async def create_tables():
    """
    Create all tables from models.
    Use this for development. In production, use migrations.

    Example:
        await create_tables()
    """
    engine = init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """
    Drop all tables.
    ⚠️ DANGEROUS: Only use in development/testing!

    Example:
        await drop_tables()
    """
    engine = init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
