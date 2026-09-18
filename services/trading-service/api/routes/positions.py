"""
Position Routes
API endpoints for position management
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

import sys
sys.path.append('/app')

from shared.database.connection import get_db_session
from services.trading_service.repositories.position_repository import PositionRepository
from services.trading_service.services.position_service import PositionService
from services.trading_service.api.schemas.trading import (
    CreatePositionRequest,
    PositionResponse,
    UpdatePositionPriceRequest,
    ClosePositionRequest,
    PortfolioSummaryResponse
)

router = APIRouter(prefix="/positions", tags=["positions"])


def get_position_service(session: AsyncSession = Depends(get_db_session)) -> PositionService:
    """Dependency injection for PositionService."""
    position_repo = PositionRepository(session)
    return PositionService(position_repo)


def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from header (set by API Gateway)."""
    return x_user_id


@router.get("/", response_model=List[PositionResponse])
async def get_positions(
    user_id: str = Depends(get_user_id),
    position_service: PositionService = Depends(get_position_service)
):
    """Get all open positions for user."""
    positions = await position_service.get_user_positions(user_id)
    return positions


@router.post("/", response_model=PositionResponse, status_code=status.HTTP_201_CREATED)
async def create_position(
    request: CreatePositionRequest,
    user_id: str = Depends(get_user_id),
    position_service: PositionService = Depends(get_position_service)
):
    """Create new position."""
    position = await position_service.create_position(
        user_id=user_id,
        symbol=request.symbol,
        asset_class=request.asset_class.value,
        side=request.side.value,
        quantity=request.quantity,
        entry_price=request.entry_price,
        broker=request.broker,
        strategy_id=request.strategy_id,
        stop_loss_price=request.stop_loss_price,
        take_profit_price=request.take_profit_price
    )
    return position


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: str,
    user_id: str = Depends(get_user_id),
    position_service: PositionService = Depends(get_position_service)
):
    """Get position by ID."""
    position = await position_service.get_position_by_id(user_id, position_id)
    return position


@router.patch("/{position_id}/price", response_model=PositionResponse)
async def update_position_price(
    position_id: str,
    request: UpdatePositionPriceRequest,
    position_service: PositionService = Depends(get_position_service)
):
    """Update position with latest market price."""
    position = await position_service.update_position_price(
        position_id,
        request.current_price
    )
    return position


@router.post("/{position_id}/close", response_model=PositionResponse)
async def close_position(
    position_id: str,
    request: ClosePositionRequest,
    user_id: str = Depends(get_user_id),
    position_service: PositionService = Depends(get_position_service)
):
    """Close position."""
    position = await position_service.close_position(
        user_id,
        position_id,
        request.close_price
    )
    return position
