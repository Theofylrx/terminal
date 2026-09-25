"""
Position Service
Business logic for position management
"""

from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models.position import Position, PositionStatus, PositionSide, AssetClass
from shared.events.event_bus import EventPublisher
from shared.events.event_types import EventType
from ..repositories.position_repository import PositionRepository


class PositionService:
    """
    Position service handling position business logic.
    """

    def __init__(
        self,
        position_repo: PositionRepository,
        event_publisher: Optional[EventPublisher] = None
    ):
        """
        Initialize position service.

        Args:
            position_repo: Position repository
            event_publisher: Optional event publisher for notifications
        """
        self.position_repo = position_repo
        self.event_publisher = event_publisher

    async def get_user_positions(self, user_id: str) -> List[Position]:
        """
        Get all open positions for user.

        Args:
            user_id: User ID

        Returns:
            List of positions

        Example:
            positions = await position_service.get_user_positions("user-123")
        """
        return await self.position_repo.get_open_positions(user_id)

    async def get_position_by_id(
        self,
        user_id: str,
        position_id: str
    ) -> Position:
        """
        Get position by ID.

        Args:
            user_id: User ID
            position_id: Position ID

        Returns:
            Position

        Raises:
            HTTPException: If position not found or doesn't belong to user

        Example:
            position = await position_service.get_position_by_id("user-123", "pos-456")
        """
        position = await self.position_repo.get_by_id(position_id)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )

        if position.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this position"
            )

        return position

    async def get_position_by_symbol(
        self,
        user_id: str,
        symbol: str
    ) -> Optional[Position]:
        """
        Get open position by symbol.

        Args:
            user_id: User ID
            symbol: Trading symbol

        Returns:
            Position if found, None otherwise

        Example:
            position = await position_service.get_position_by_symbol("user-123", "BTCUSDT")
        """
        return await self.position_repo.get_position_by_symbol(user_id, symbol)

    async def create_position(
        self,
        user_id: str,
        symbol: str,
        asset_class: AssetClass,
        side: PositionSide,
        quantity: float,
        entry_price: float,
        broker: str,
        strategy_id: Optional[str] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> Position:
        """
        Create new position.

        Args:
            user_id: User ID
            symbol: Trading symbol
            asset_class: Asset class
            side: LONG or SHORT
            quantity: Position size
            entry_price: Entry price
            broker: Broker name
            strategy_id: Optional strategy ID
            stop_loss_price: Optional stop loss
            take_profit_price: Optional take profit

        Returns:
            Created position

        Raises:
            HTTPException: If position already exists for symbol

        Example:
            position = await position_service.create_position(
                user_id="user-123",
                symbol="BTCUSDT",
                asset_class=AssetClass.CRYPTO,
                side=PositionSide.LONG,
                quantity=0.5,
                entry_price=50000.0,
                broker="binance"
            )
        """
        # Check if position already exists
        existing = await self.get_position_by_symbol(user_id, symbol)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position already exists for {symbol}"
            )

        # Calculate cost basis
        cost_basis = entry_price * quantity

        # Create position
        position = await self.position_repo.create(
            user_id=user_id,
            symbol=symbol,
            asset_class=asset_class,
            side=side,
            status=PositionStatus.OPEN,
            quantity=quantity,
            avg_entry_price=entry_price,
            current_price=entry_price,
            market_value=cost_basis,
            cost_basis=cost_basis,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            broker=broker,
            strategy_id=strategy_id,
            stop_loss_price=stop_loss_price,
            take_profit_price=take_profit_price
        )

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.POSITION_OPENED.value,
                {
                    "position_id": position.id,
                    "user_id": user_id,
                    "symbol": symbol,
                    "side": side.value,
                    "quantity": quantity,
                    "entry_price": entry_price
                }
            )

        return position

    async def update_position_price(
        self,
        position_id: str,
        current_price: float
    ) -> Position:
        """
        Update position with latest market price.

        Args:
            position_id: Position ID
            current_price: Latest market price

        Returns:
            Updated position

        Example:
            position = await position_service.update_position_price("pos-123", 51000.0)
        """
        position = await self.position_repo.update_position_price(position_id, current_price)

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )

        # Check stop loss / take profit
        if position.is_stop_loss_triggered():
            # TODO: Trigger close position order
            pass

        if position.is_take_profit_triggered():
            # TODO: Trigger close position order
            pass

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.POSITION_UPDATED.value,
                {
                    "position_id": position.id,
                    "symbol": position.symbol,
                    "current_price": current_price,
                    "unrealized_pnl": position.unrealized_pnl,
                    "market_value": position.market_value
                }
            )

        return position

    async def close_position(
        self,
        user_id: str,
        position_id: str,
        close_price: float
    ) -> Position:
        """
        Close position.

        Args:
            user_id: User ID
            position_id: Position ID
            close_price: Closing price

        Returns:
            Closed position

        Example:
            position = await position_service.close_position("user-123", "pos-456", 52000.0)
        """
        # Get position
        position = await self.get_position_by_id(user_id, position_id)

        if position.status != PositionStatus.OPEN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Position is not open"
            )

        # Close position
        closed_position = await self.position_repo.close_position(position_id, close_price)

        # Publish event
        if self.event_publisher:
            await self.event_publisher.publish(
                EventType.POSITION_CLOSED.value,
                {
                    "position_id": closed_position.id,
                    "user_id": user_id,
                    "symbol": closed_position.symbol,
                    "close_price": close_price,
                    "realized_pnl": closed_position.realized_pnl
                }
            )

        return closed_position

    async def get_portfolio_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get portfolio summary with metrics.

        Args:
            user_id: User ID

        Returns:
            Portfolio summary

        Example:
            summary = await position_service.get_portfolio_summary("user-123")
        """
        # Get positions
        positions = await self.position_repo.get_open_positions(user_id)

        # Calculate metrics
        total_value = sum(p.market_value for p in positions)
        total_cost = sum(p.cost_basis for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        position_count = len(positions)

        # Calculate by asset class
        by_asset_class = {}
        for asset_class in AssetClass:
            positions_by_class = [p for p in positions if p.asset_class == asset_class]
            if positions_by_class:
                by_asset_class[asset_class.value] = {
                    "count": len(positions_by_class),
                    "value": sum(p.market_value for p in positions_by_class),
                    "pnl": sum(p.unrealized_pnl for p in positions_by_class)
                }

        return {
            "total_value": total_value,
            "total_cost": total_cost,
            "total_unrealized_pnl": total_pnl,
            "total_pnl_percentage": (total_pnl / total_cost * 100) if total_cost > 0 else 0,
            "position_count": position_count,
            "by_asset_class": by_asset_class,
            "positions": [p.to_dict() for p in positions]
        }

    async def get_closed_positions(
        self,
        user_id: str,
        limit: int = 100
    ) -> List[Position]:
        """
        Get trade history (closed positions).

        Args:
            user_id: User ID
            limit: Maximum results

        Returns:
            List of closed positions

        Example:
            history = await position_service.get_closed_positions("user-123", limit=50)
        """
        return await self.position_repo.get_closed_positions(user_id, limit)
