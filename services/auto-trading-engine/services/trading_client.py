"""
Trading Service Client
Calls Trading Service for position and order data
"""

import logging
from typing import Optional, Dict, Any, List

from .http_client import HTTPClient
from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.trading_client")


class TradingClient:
    """Client for Trading Service."""

    def __init__(self):
        """Initialize Trading client."""
        self.client = HTTPClient(
            base_url=settings.TRADING_SERVICE_URL,
            service_name="TradingService"
        )

    async def get_open_positions(
        self,
        user_id: Optional[str] = None,
        auto_trade_only: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get open positions.

        Args:
            user_id: Filter by user ID (optional)
            auto_trade_only: Only return auto-traded positions

        Returns:
            List of open positions
        """
        logger.debug(f"📊 Getting open positions (auto_trade_only={auto_trade_only})")

        params = {}
        if user_id:
            params["user_id"] = user_id
        if auto_trade_only:
            params["auto_trade"] = "true"
        params["status"] = "OPEN"

        response = await self.client.get("/api/v1/positions", params=params)

        if response:
            positions = response.get("positions", [])
            logger.info(f"✅ Retrieved {len(positions)} open positions")
            return positions
        else:
            logger.warning("⚠️  Failed to get open positions")
            return []

    async def get_position(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Get position by ID.

        Args:
            position_id: Position ID

        Returns:
            Position data if found
        """
        logger.debug(f"📊 Getting position {position_id}")

        response = await self.client.get(f"/api/v1/positions/{position_id}")

        if response:
            logger.debug(f"✅ Position retrieved: {position_id}")
            return response
        else:
            logger.warning(f"⚠️  Failed to get position {position_id}")
            return None

    async def calculate_pnl(
        self,
        position_id: str,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate current P&L for a position.

        Args:
            position_id: Position ID
            current_price: Current market price

        Returns:
            P&L data:
            {
                "pnl": 225.50,
                "pnl_percent": 5.2,
                "unrealized_pnl": 225.50,
                "cost_basis": 4500.00,
                "current_value": 4725.50
            }
        """
        logger.debug(f"💰 Calculating P&L for {position_id} at ${current_price}")

        response = await self.client.post(
            f"/api/v1/positions/{position_id}/pnl",
            json_data={"current_price": current_price}
        )

        if response:
            logger.debug(
                f"✅ P&L calculated: {response.get('pnl_percent')}%"
            )
            return response
        else:
            logger.warning(f"⚠️  Failed to calculate P&L for {position_id}")
            return None

    async def get_user_capital(self, user_id: str) -> Optional[float]:
        """
        Get user's current capital.

        Args:
            user_id: User ID

        Returns:
            Current capital amount
        """
        logger.debug(f"💵 Getting capital for user {user_id}")

        response = await self.client.get(f"/api/v1/users/{user_id}/capital")

        if response:
            capital = response.get("current_capital")
            logger.debug(f"✅ User capital: ${capital}")
            return capital
        else:
            logger.warning(f"⚠️  Failed to get user capital")
            return None

    async def close(self):
        """Close client."""
        await self.client.close()
