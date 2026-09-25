"""
Order Repository
Handles database operations for orders
"""

from typing import List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

import sys
sys.path.append('/Users/likhobomvana/terminal')

from shared.database.models.order import Order, OrderStatus


class OrderRepository:
    """Repository for order database operations."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    async def create(self, order: Order) -> Order:
        """
        Create new order.

        Args:
            order: Order instance

        Returns:
            Created order
        """
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_by_id(self, order_id: str) -> Optional[Order]:
        """
        Get order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_by_broker_order_id(
        self, broker_order_id: str, broker: str
    ) -> Optional[Order]:
        """
        Get order by broker order ID.

        Args:
            broker_order_id: Broker's order ID
            broker: Broker name

        Returns:
            Order if found, None otherwise
        """
        result = await self.session.execute(
            select(Order).where(
                and_(
                    Order.broker_order_id == broker_order_id,
                    Order.broker == broker
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_user_orders(
        self,
        user_id: str,
        status: Optional[OrderStatus] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders for a user.

        Args:
            user_id: User ID
            status: Filter by status (optional)
            symbol: Filter by symbol (optional)
            limit: Maximum number of orders

        Returns:
            List of orders
        """
        query = select(Order).where(Order.user_id == user_id)

        if status:
            query = query.where(Order.status == status)

        if symbol:
            query = query.where(Order.symbol == symbol)

        query = query.order_by(desc(Order.created_at)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_orders(self, user_id: str) -> List[Order]:
        """
        Get all active (non-terminal) orders for a user.

        Args:
            user_id: User ID

        Returns:
            List of active orders
        """
        result = await self.session.execute(
            select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_([
                        OrderStatus.PENDING,
                        OrderStatus.SUBMITTED,
                        OrderStatus.ACCEPTED,
                        OrderStatus.PARTIALLY_FILLED
                    ])
                )
            )
        )
        return list(result.scalars().all())

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        filled_quantity: Optional[float] = None,
        avg_fill_price: Optional[float] = None,
        filled_at: Optional[datetime] = None
    ) -> Optional[Order]:
        """
        Update order status.

        Args:
            order_id: Order ID
            status: New status
            filled_quantity: Filled quantity (optional)
            avg_fill_price: Average fill price (optional)
            filled_at: Fill timestamp (optional)

        Returns:
            Updated order or None if not found
        """
        order = await self.get_by_id(order_id)
        if not order:
            return None

        order.status = status

        if filled_quantity is not None:
            order.filled_quantity = filled_quantity

        if avg_fill_price is not None:
            order.avg_fill_price = avg_fill_price

        if filled_at is not None:
            order.filled_at = filled_at

        order.updated_at = datetime.utcnow()

        await self.session.commit()
        await self.session.refresh(order)
        return order

    async def get_daily_trade_count(self, user_id: str) -> int:
        """
        Get number of trades today for a user.

        Args:
            user_id: User ID

        Returns:
            Trade count
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        result = await self.session.execute(
            select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status == OrderStatus.FILLED,
                    Order.filled_at >= today_start
                )
            )
        )

        return len(list(result.scalars().all()))

    async def delete(self, order_id: str) -> bool:
        """
        Delete an order.

        Args:
            order_id: Order ID

        Returns:
            True if deleted, False if not found
        """
        order = await self.get_by_id(order_id)
        if not order:
            return False

        await self.session.delete(order)
        await self.session.commit()
        return True
