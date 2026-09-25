"""
Portfolio Routes
API endpoints for portfolio management
"""

from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.database.connection import get_db_session
from ...repositories.position_repository import PositionRepository
from ...services.position_service import PositionService
from ..schemas.trading import (
    PortfolioSummaryResponse,
    PositionResponse
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


def get_position_service(session: AsyncSession = Depends(get_db_session)) -> PositionService:
    """Dependency injection for PositionService."""
    position_repo = PositionRepository(session)
    return PositionService(position_repo)


def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from header (set by API Gateway)."""
    return x_user_id


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    user_id: str = Depends(get_user_id),
    position_service: PositionService = Depends(get_position_service)
):
    """
    Get portfolio summary with metrics.

    Returns:
        - Total market value
        - Total unrealized P&L
        - Position count
        - Breakdown by asset class
        - List of all positions
    """
    summary = await position_service.get_portfolio_summary(user_id)
    return summary


@router.get("/history", response_model=List[PositionResponse])
async def get_trade_history(
    user_id: str = Depends(get_user_id),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    position_service: PositionService = Depends(get_position_service)
):
    """Get trade history (closed positions)."""
    positions = await position_service.get_closed_positions(user_id, limit)
    return positions
