"""
Order Service
Business logic for order management
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models.order import Order, OrderStatus, OrderSide, OrderType, TimeInForce
from shared.events.event_bus import EventPublisher
from shared.events.event_types import EventType
from ..repositories.order_repository import OrderRepository


class OrderService:
    """
    Order service handling order business logic.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        event_publisher: Optional[EventPublisher] = None
    ):
        """
        Initialize order service.

        Args:
            order_repo: Order repository
            event_publisher: Optional event publisher
        """
        self.order_repo = order_repo
        self.event_publisher = event_publisher

    async def create_order(
        self,
        user_id: str,
        symbol: str,
        asset_class: str,
        order_type: OrderType,
        side: OrderSide,
        quantity: float,
        broker: str,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.GTC,
        position_id: Optional[str] = None,
        strategy_id: Optional[str] = None
    ) -> Order:
        """
        Create new order.

        Args:
            user_id: User ID
            symbol: Trading symbol
            asset_class: Asset class
            order_type: Order type (MARKET, LIMIT, etc.)
            side: BUY or SELL
            quantity: Order quantity
            broker: Broker name
            limit_price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            time_in_force: Time in force
            position_id: Associated position
            strategy_id: Strategy ID

        Returns:
            Created order

        Raises:
            HTTPException: If validation fails

        Example:
            order = await order_service.create_order(
                user_id="user-123",
                symbol="BTCUSDT",
                asset_class="CRYPTO",
                order_type=OrderType.LIMIT,
                side=OrderSide.BUY,
                quantity=0.5,
                limit_price=49000.0,
                broker="binance"
            )
        """
        # Validate order type and prices
        if order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT] and not limit_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit price required for LIMIT orders"
            )

        if order_type in [OrderType.STOP_LOSS, OrderType.STOP_LIMIT, OrderType.TRAILING_STOP] and not stop_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stop price required for STOP orders"
            )

        # Create order
        order = await self.order_repo.create(
            user_id=user_id,
            position_id=position_id,
            symbol=symbol,
            asset_class=asset_class,
            order_type=order_type,
            side=side,
            status=OrderStatus.PENDING,
            quantity=quantity,
            filled_quantity=0.0,
            limit_price=limit_price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            broker=broker,
            strategy_id=strategy_id
        )

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.ORDER_CREATED.value,
                {
                    "order_id": order.id,
                    "user_id": user_id,
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": quantity,
                    "order_type": order_type.value
                }
            )

        return order

    async def get_order_by_id(self, user_id: str, order_id: str) -> Order:
        """
        Get order by ID.

        Args:
            user_id: User ID
            order_id: Order ID

        Returns:
            Order

        Raises:
            HTTPException: If order not found or doesn't belong to user

        Example:
            order = await order_service.get_order_by_id("user-123", "order-456")
        """
        order = await self.order_repo.get_by_id(order_id)

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )

        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this order"
            )

        return order

    async def get_user_orders(
        self,
        user_id: str,
        active_only: bool = False,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Order]:
        """
        Get user orders.

        Args:
            user_id: User ID
            active_only: Only return active orders
            symbol: Filter by symbol
            limit: Maximum results

        Returns:
            List of orders

        Example:
            orders = await order_service.get_user_orders("user-123", active_only=True)
        """
        if active_only:
            return await self.order_repo.get_active_orders(user_id)
        elif symbol:
            return await self.order_repo.get_orders_by_symbol(user_id, symbol, limit)
        else:
            return await self.order_repo.get_all(
                filters={"user_id": user_id},
                limit=limit,
                order_by="-created_at"
            )

    async def submit_order(self, order_id: str, broker_order_id: str) -> Order:
        """
        Mark order as submitted to broker.

        Args:
            order_id: Order ID
            broker_order_id: Order ID from broker

        Returns:
            Updated order

        Example:
            order = await order_service.submit_order("order-123", "broker-order-456")
        """
        order = await self.order_repo.update_order_status(
            order_id,
            OrderStatus.SUBMITTED,
            broker_order_id=broker_order_id
        )

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.ORDER_SUBMITTED.value,
                {
                    "order_id": order.id,
                    "broker_order_id": broker_order_id,
                    "symbol": order.symbol
                }
            )

        return order

    async def mark_order_filled(
        self,
        order_id: str,
        filled_quantity: float,
        avg_fill_price: float,
        commission: float = 0.0,
        slippage: float = 0.0
    ) -> Order:
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
            order = await order_service.mark_order_filled(
                "order-123",
                filled_quantity=0.5,
                avg_fill_price=50100.0,
                commission=25.0
            )
        """
        order = await self.order_repo.mark_filled(
            order_id,
            filled_quantity,
            avg_fill_price,
            commission,
            slippage
        )

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.ORDER_FILLED.value,
                {
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "side": order.side.value,
                    "filled_quantity": filled_quantity,
                    "avg_fill_price": avg_fill_price,
                    "commission": commission
                }
            )

        return order

    async def cancel_order(self, user_id: str, order_id: str) -> Order:
        """
        Cancel order.

        Args:
            user_id: User ID
            order_id: Order ID

        Returns:
            Cancelled order

        Raises:
            HTTPException: If order cannot be cancelled

        Example:
            order = await order_service.cancel_order("user-123", "order-456")
        """
        # Get order
        order = await self.get_order_by_id(user_id, order_id)

        # Check if order can be cancelled
        if not order.is_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order cannot be cancelled (already completed)"
            )

        # Cancel order
        cancelled_order = await self.order_repo.cancel_order(order_id)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.ORDER_CANCELLED.value,
                {
                    "order_id": order.id,
                    "symbol": order.symbol,
                    "user_id": user_id
                }
            )

        return cancelled_order

    async def get_order_history(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Order]:
        """
        Get order history (completed orders).

        Args:
            user_id: User ID
            limit: Maximum results

        Returns:
            List of completed orders

        Example:
            history = await order_service.get_order_history("user-123", limit=50)
        """
        return await self.order_repo.get_order_history(user_id, limit)
