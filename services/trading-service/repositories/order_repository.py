"""
Order Repository
Data access layer for Order model with order-specific queries
"""

from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

import sys
sys.path.append('/app')

from shared.database.base_repository import BaseRepository
from shared.database.models.order import Order, OrderStatus, OrderSide, OrderType


class OrderRepository(BaseRepository[Order]):
    """
    Repository for Order model with order operations.
    Extends BaseRepository for common CRUD operations.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize order repository.

        Args:
            session: Async database session
        """
        super().__init__(Order, session)

    async def get_active_orders(self, user_id: str) -> List[Order]:
        """
        Get all active (not completed) orders for a user.

        Args:
            user_id: User ID

        Returns:
            List of active orders

        Example:
            orders = await order_repo.get_active_orders("user-123")
        """
        query = select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.status.in_([
                    OrderStatus.PENDING,
                    OrderStatus.SUBMITTED,
                    OrderStatus.ACCEPTED,
                    OrderStatus.PARTIALLY_FILLED
                ])
            )
        ).order_by(Order.created_at.desc())

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_orders_by_symbol(
        self,
        user_id: str,
        symbol: str,
        limit: int = 100
    ) -> List[Order]:
        """
        Get orders for specific symbol.

        Args:
            user_id: User ID
            symbol: Trading symbol
            limit: Maximum number of orders

        Returns:
            List of orders

        Example:
            orders = await order_repo.get_orders_by_symbol("user-123", "BTCUSDT")
        """
        query = select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.symbol == symbol
            )
        ).order_by(Order.created_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_order_by_broker_id(
        self,
        broker_order_id: str
    ) -> Optional[Order]:
        """
        Get order by broker order ID.

        Args:
            broker_order_id: Order ID from broker

        Returns:
            Order if found, None otherwise

        Example:
            order = await order_repo.get_order_by_broker_id("broker-order-456")
        """
        query = select(Order).where(Order.broker_order_id == broker_order_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_order_status(
        self,
        order_id: str,
        status: OrderStatus,
        **kwargs
    ) -> Optional[Order]:
        """
        Update order status and optional fields.

        Args:
            order_id: Order ID
            status: New status
            **kwargs: Additional fields to update

        Returns:
            Updated order

        Example:
            order = await order_repo.update_order_status(
                "order-123",
                OrderStatus.FILLED,
                filled_quantity=0.5,
                avg_fill_price=50100.0
            )
        """
        update_data = {"status": status, **kwargs}

        # Set timestamps based on status
        if status == OrderStatus.SUBMITTED and "submitted_at" not in kwargs:
            update_data["submitted_at"] = datetime.utcnow()
        elif status == OrderStatus.FILLED and "filled_at" not in kwargs:
            update_data["filled_at"] = datetime.utcnow()

        return await self.update(order_id, **update_data)

    async def mark_filled(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float,
        commission: float = 0.0,
        slippage: float = 0.0
    ) -> Optional[Order]:
        """
        Mark order as filled.

        Args:
            order_id: Order ID
            filled_quantity: Quantity filled
            avg_fill_price: Average fill price
            commission: Trading commission
            slippage: Price slippage

        Returns:
            Updated order

        Example:
            order = await order_repo.mark_filled(
                "order-123",
                filled_quantity=0.5,
                avg_fill_price=50100.0,
                commission=25.0
            )
        """
        return await self.update_order_status(
            order_id,
            OrderStatus.FILLED,
            filled_quantity=filled_quantity,
            avg_fill_price=avg_fill_price,
            commission=commission,
            slippage=slippage,
            filled_at=datetime.utcnow()
        )

    async def mark_partially_filled(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float
    ) -> Optional[Order]:
        """
        Mark order as partially filled.

        Args:
            order_id: Order ID
            filled_quantity: Quantity filled so far
            avg_fill_price: Average fill price

        Returns:
            Updated order

        Example:
            order = await order_repo.mark_partially_filled(
                "order-123",
                filled_quantity=0.25,
                avg_fill_price=50050.0
            )
        """
        return await self.update_order_status(
            order_id,
            OrderStatus.PARTIALLY_FILLED,
            filled_quantity=filled_quantity,
            avg_fill_price=avg_fill_price
        )

    async def cancel_order(self, order_id: str) -> Optional[Order]:
        """
        Cancel order.

        Args:
            order_id: Order ID

        Returns:
            Cancelled order

        Example:
            order = await order_repo.cancel_order("order-123")
        """
        return await self.update_order_status(order_id, OrderStatus.CANCELLED)

    async def reject_order(self, order_id: str, reason: str = None) -> Optional[Order]:
        """
        Mark order as rejected.

        Args:
            order_id: Order ID
            reason: Rejection reason

        Returns:
            Rejected order

        Example:
            order = await order_repo.reject_order("order-123", "Insufficient funds")
        """
        return await self.update_order_status(order_id, OrderStatus.REJECTED)

    async def get_order_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Order]:
        """
        Get order history (completed orders).

        Args:
            user_id: User ID
            limit: Maximum number of orders

        Returns:
            List of completed orders

        Example:
            history = await order_repo.get_order_history("user-123", limit=50)
        """
        query = select(Order).where(
            and_(
                Order.user_id == user_id,
                Order.status.in_([
                    OrderStatus.FILLED,
                    OrderStatus.CANCELLED,
                    OrderStatus.REJECTED,
                    OrderStatus.EXPIRED
                ])
            )
        ).order_by(Order.updated_at.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())
