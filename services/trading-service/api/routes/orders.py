"""
Order Routes
API endpoints for order management
"""

from typing import List
from fastapi import APIRouter, Depends, Query, status, Header
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from shared.database.connection import get_db_session
from ...repositories.order_repository import OrderRepository
from ...services.order_service import OrderService
from ..schemas.trading import (
    CreateOrderRequest,
    OrderResponse,
    MessageResponse
)

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_service(session: AsyncSession = Depends(get_db_session)) -> OrderService:
    """Dependency injection for OrderService."""
    order_repo = OrderRepository(session)
    return OrderService(order_repo)


def get_user_id(x_user_id: str = Header(...)) -> str:
    """Extract user ID from header (set by API Gateway)."""
    return x_user_id


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    user_id: str = Depends(get_user_id),
    active_only: bool = Query(False, description="Only return active orders"),
    symbol: str = Query(None, description="Filter by symbol"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    order_service: OrderService = Depends(get_order_service)
):
    """Get user orders."""
    orders = await order_service.get_user_orders(
        user_id,
        active_only=active_only,
        symbol=symbol,
        limit=limit
    )
    return orders


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service)
):
    """Create new order."""
    order = await order_service.create_order(
        user_id=user_id,
        symbol=request.symbol,
        asset_class=request.asset_class.value,
        order_type=request.order_type.value,
        side=request.side.value,
        quantity=request.quantity,
        broker=request.broker,
        limit_price=request.limit_price,
        stop_price=request.stop_price,
        time_in_force=request.time_in_force.value,
        position_id=request.position_id,
        strategy_id=request.strategy_id
    )
    return order


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order by ID."""
    order = await order_service.get_order_by_id(user_id, order_id)
    return order


@router.delete("/{order_id}", response_model=MessageResponse)
async def cancel_order(
    order_id: str,
    user_id: str = Depends(get_user_id),
    order_service: OrderService = Depends(get_order_service)
):
    """Cancel order."""
    order = await order_service.cancel_order(user_id, order_id)
    return MessageResponse(
        message="Order cancelled successfully",
        detail=f"Order {order.id} cancelled"
    )


@router.get("/history/all", response_model=List[OrderResponse])
async def get_order_history(
    user_id: str = Depends(get_user_id),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    order_service: OrderService = Depends(get_order_service)
):
    """Get order history (completed orders)."""
    orders = await order_service.get_order_history(user_id, limit)
    return orders
