"""
Auto-Trading Configuration API Routes
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from shared.database.connection import get_db_session
from shared.database.models.auto_trading_config import AutoTradingConfig, StrategyType
from shared.database.models.auto_trading_session import AutoTradingSession
from ...repositories import AutoTradingConfigRepository, AutoTradingSessionRepository
from ..schemas.config_schemas import (
    AutoTradingConfigCreate,
    AutoTradingConfigUpdate,
    AutoTradingConfigResponse,
    SessionStatsResponse
)

logger = logging.getLogger("auto-trading-engine.api.config")

router = APIRouter(prefix="/api/v1/config", tags=["Auto-Trading Configuration"])


@router.post("", response_model=AutoTradingConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_config(
    user_id: str,
    config_data: AutoTradingConfigCreate,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Create new auto-trading configuration for a symbol.

    Args:
        user_id: User ID
        config_data: Configuration data
        session: Database session

    Returns:
        Created configuration
    """
    logger.info(f"Creating auto-trading config for {config_data.symbol} (user: {user_id})")

    repo = AutoTradingConfigRepository(session)

    # Check if config already exists
    existing = await repo.get_by_user_and_symbol(user_id, config_data.symbol)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Configuration for {config_data.symbol} already exists"
        )

    # Create new configuration
    config = AutoTradingConfig(
        user_id=user_id,
        symbol=config_data.symbol,
        broker=config_data.broker,
        asset_class=config_data.asset_class,
        enabled=False,  # Start disabled by default
        risk_per_trade_percent=config_data.risk_per_trade_percent,
        max_concurrent_positions=config_data.max_concurrent_positions,
        max_daily_loss_percent=config_data.max_daily_loss_percent,
        stop_loss_percent=config_data.stop_loss_percent,
        strategy_type=StrategyType(config_data.strategy_type),
        entry_confidence_threshold=config_data.entry_confidence_threshold,
        trading_start_hour=config_data.trading_start_hour,
        trading_end_hour=config_data.trading_end_hour,
        auto_close_on_correction=config_data.auto_close_on_correction,
        trailing_stop_enabled=config_data.trailing_stop_enabled,
        trailing_stop_percent=config_data.trailing_stop_percent
    )

    created_config = await repo.create(config)

    logger.info(f"✅ Created config for {config_data.symbol} (id: {created_config.id})")

    return created_config


@router.get("", response_model=List[AutoTradingConfigResponse])
async def get_user_configs(
    user_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get all auto-trading configurations for a user.

    Args:
        user_id: User ID
        session: Database session

    Returns:
        List of configurations
    """
    repo = AutoTradingConfigRepository(session)
    configs = await repo.get_all_by_user(user_id)

    return configs


@router.get("/{config_id}", response_model=AutoTradingConfigResponse)
async def get_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get auto-trading configuration by ID.

    Args:
        config_id: Configuration ID
        session: Database session

    Returns:
        Configuration
    """
    repo = AutoTradingConfigRepository(session)
    config = await repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    return config


@router.patch("/{config_id}", response_model=AutoTradingConfigResponse)
async def update_config(
    config_id: str,
    config_updates: AutoTradingConfigUpdate,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Update auto-trading configuration.

    Args:
        config_id: Configuration ID
        config_updates: Configuration updates
        session: Database session

    Returns:
        Updated configuration
    """
    logger.info(f"Updating config {config_id}")

    repo = AutoTradingConfigRepository(session)
    config = await repo.get_by_id(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    # Apply updates
    update_data = config_updates.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "strategy_type":
            setattr(config, field, StrategyType(value))
        else:
            setattr(config, field, value)

    updated_config = await repo.update(config)

    logger.info(f"✅ Updated config {config_id}")

    return updated_config


@router.post("/{config_id}/enable", response_model=AutoTradingConfigResponse)
async def enable_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Enable auto-trading for a configuration.

    Args:
        config_id: Configuration ID
        session: Database session

    Returns:
        Updated configuration
    """
    logger.info(f"Enabling auto-trading for config {config_id}")

    repo = AutoTradingConfigRepository(session)
    config = await repo.enable(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    # Create new session
    session_repo = AutoTradingSessionRepository(session)
    new_session = AutoTradingSession(
        config_id=config.id,
        user_id=config.user_id,
        symbol=config.symbol
    )
    await session_repo.create(new_session)

    logger.info(f"✅ Enabled auto-trading for {config.symbol}")

    return config


@router.post("/{config_id}/disable", response_model=AutoTradingConfigResponse)
async def disable_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Disable auto-trading for a configuration.

    Args:
        config_id: Configuration ID
        session: Database session

    Returns:
        Updated configuration
    """
    logger.info(f"Disabling auto-trading for config {config_id}")

    repo = AutoTradingConfigRepository(session)
    config = await repo.disable(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    # Stop active session
    session_repo = AutoTradingSessionRepository(session)
    active_session = await session_repo.get_by_config(config_id)
    if active_session:
        await session_repo.stop(active_session.id)

    logger.info(f"✅ Disabled auto-trading for {config.symbol}")

    return config


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Delete auto-trading configuration.

    Args:
        config_id: Configuration ID
        session: Database session
    """
    logger.info(f"Deleting config {config_id}")

    repo = AutoTradingConfigRepository(session)
    deleted = await repo.delete(config_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration {config_id} not found"
        )

    logger.info(f"✅ Deleted config {config_id}")


@router.get("/{config_id}/session", response_model=SessionStatsResponse)
async def get_session_stats(
    config_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Get session statistics for a configuration.

    Args:
        config_id: Configuration ID
        session: Database session

    Returns:
        Session statistics
    """
    session_repo = AutoTradingSessionRepository(session)
    session_obj = await session_repo.get_by_config(config_id)

    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active session for configuration {config_id}"
        )

    # Calculate win rate
    win_rate = session_obj.calculate_win_rate()

    return SessionStatsResponse(
        id=session_obj.id,
        symbol=session_obj.symbol,
        status=session_obj.status.value,
        total_trades=session_obj.total_trades,
        winning_trades=session_obj.winning_trades,
        losing_trades=session_obj.losing_trades,
        win_rate=win_rate,
        total_pnl=session_obj.total_pnl,
        best_trade_pnl=session_obj.best_trade_pnl,
        worst_trade_pnl=session_obj.worst_trade_pnl,
        current_open_positions=session_obj.current_open_positions,
        daily_loss=session_obj.daily_loss,
        started_at=session_obj.started_at,
        last_activity_at=session_obj.last_activity_at
    )
