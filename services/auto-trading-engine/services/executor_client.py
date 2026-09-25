"""
Executor Service Client
Calls Executor Service for order execution and position sizing
"""

import logging
from typing import Optional, Dict, Any

from .http_client import HTTPClient
from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.executor_client")


class ExecutorClient:
    """Client for Executor Service."""

    def __init__(self):
        """Initialize Executor client."""
        self.client = HTTPClient(
            base_url=settings.EXECUTOR_SERVICE_URL,
            service_name="ExecutorService"
        )

    async def calculate_position_size(
        self,
        user_id: str,
        symbol: str,
        entry_price: float,
        risk_percent: float,
        stop_loss_percent: float
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate optimal position size.

        Args:
            user_id: User ID
            symbol: Trading symbol
            entry_price: Entry price
            risk_percent: Percent of capital to risk
            stop_loss_percent: Stop loss percentage from entry

        Returns:
            Position sizing data:
            {
                "quantity": 33.33,
                "position_value": 5000.00,
                "risk_amount": 100.00,
                "stop_loss_price": 147.00,
                "take_profit_price": 158.00
            }
        """
        logger.debug(f"📐 Calculating position size for {symbol}")

        response = await self.client.post(
            "/api/v1/position-size",
            json_data={
                "user_id": user_id,
                "symbol": symbol,
                "entry_price": entry_price,
                "risk_percent": risk_percent,
                "stop_loss_percent": stop_loss_percent
            }
        )

        if response:
            logger.info(
                f"✅ Position size for {symbol}: {response.get('quantity')} units "
                f"(${response.get('position_value')})"
            )
            return response
        else:
            logger.warning(f"⚠️  Failed to calculate position size for {symbol}")
            return None

    async def execute_market_order(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute market order.

        Args:
            user_id: User ID
            symbol: Trading symbol
            side: Order side (BUY/SELL, LONG/SHORT)
            quantity: Order quantity
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            metadata: Additional metadata (e.g., auto_trade flag)

        Returns:
            Order execution result
        """
        logger.info(f"🎯 Executing {side} order for {symbol}: {quantity} units")

        response = await self.client.post(
            "/api/v1/orders/market",
            json_data={
                "user_id": user_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "metadata": metadata or {}
            }
        )

        if response:
            logger.info(f"✅ Order executed for {symbol}: {response.get('order_id')}")
            return response
        else:
            logger.error(f"❌ Failed to execute order for {symbol}")
            return None

    async def close_position(
        self,
        position_id: str,
        reason: str,
        confidence: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Close an open position.

        Args:
            position_id: Position ID
            reason: Reason for closing
            confidence: Decision confidence (optional)

        Returns:
            Close result
        """
        logger.info(f"🔴 Closing position {position_id}: {reason}")

        response = await self.client.post(
            f"/api/v1/positions/{position_id}/close",
            json_data={
                "reason": reason,
                "confidence": confidence
            }
        )

        if response:
            logger.info(f"✅ Position closed: {position_id}")
            return response
        else:
            logger.error(f"❌ Failed to close position: {position_id}")
            return None

    async def update_stop_loss(
        self,
        position_id: str,
        new_stop_loss: float,
        reason: str = "TRAILING_STOP"
    ) -> Optional[Dict[str, Any]]:
        """
        Update stop loss for a position.

        Args:
            position_id: Position ID
            new_stop_loss: New stop loss price
            reason: Reason for adjustment

        Returns:
            Update result
        """
        logger.info(f"📊 Updating stop loss for {position_id}: ${new_stop_loss}")

        response = await self.client.post(
            f"/api/v1/positions/{position_id}/stop-loss",
            json_data={
                "stop_loss": new_stop_loss,
                "reason": reason
            }
        )

        if response:
            logger.info(f"✅ Stop loss updated for {position_id}")
            return response
        else:
            logger.warning(f"⚠️  Failed to update stop loss for {position_id}")
            return None

    async def close(self):
        """Close client."""
        await self.client.close()
