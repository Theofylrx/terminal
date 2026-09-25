"""
Notification Service Client
Calls Notification Service to send user alerts
"""

import logging
from typing import Optional, Dict, Any

from .http_client import HTTPClient
from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.notification_client")


class NotificationClient:
    """Client for Notification Service."""

    def __init__(self):
        """Initialize Notification client."""
        self.client = HTTPClient(
            base_url=settings.NOTIFICATION_SERVICE_URL,
            service_name="NotificationService"
        )

    async def send_trade_entry_notification(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        confidence: float
    ) -> bool:
        """
        Send notification for trade entry.

        Args:
            user_id: User ID
            symbol: Trading symbol
            side: Order side
            quantity: Position quantity
            entry_price: Entry price
            confidence: Signal confidence

        Returns:
            True if sent successfully
        """
        logger.debug(f"📧 Sending trade entry notification for {symbol}")

        response = await self.client.post(
            "/api/v1/notifications",
            json_data={
                "user_id": user_id,
                "type": "AUTO_TRADE_ENTRY",
                "title": f"Auto-Trade Opened: {symbol}",
                "message": f"Opened {side} position on {symbol}: {quantity} units @ ${entry_price}",
                "data": {
                    "symbol": symbol,
                    "side": side,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "confidence": confidence
                }
            }
        )

        if response:
            logger.info(f"✅ Trade entry notification sent for {symbol}")
            return True
        else:
            logger.warning(f"⚠️  Failed to send notification for {symbol}")
            return False

    async def send_trade_exit_notification(
        self,
        user_id: str,
        symbol: str,
        pnl: float,
        pnl_percent: float,
        reason: str
    ) -> bool:
        """
        Send notification for trade exit.

        Args:
            user_id: User ID
            symbol: Trading symbol
            pnl: Profit/loss amount
            pnl_percent: P&L percentage
            reason: Exit reason

        Returns:
            True if sent successfully
        """
        logger.debug(f"📧 Sending trade exit notification for {symbol}")

        emoji = "💰" if pnl > 0 else "🔴"
        pnl_sign = "+" if pnl >= 0 else ""

        response = await self.client.post(
            "/api/v1/notifications",
            json_data={
                "user_id": user_id,
                "type": "AUTO_TRADE_EXIT",
                "title": f"{emoji} Position Closed: {symbol}",
                "message": f"Closed {symbol}: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_percent:.2f}%) - {reason}",
                "data": {
                    "symbol": symbol,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "reason": reason
                }
            }
        )

        if response:
            logger.info(f"✅ Trade exit notification sent for {symbol}")
            return True
        else:
            logger.warning(f"⚠️  Failed to send notification for {symbol}")
            return False

    async def send_emergency_shutdown_notification(
        self,
        user_id: str,
        reason: str,
        total_loss: float
    ) -> bool:
        """
        Send emergency shutdown notification.

        Args:
            user_id: User ID
            reason: Shutdown reason
            total_loss: Total loss amount

        Returns:
            True if sent successfully
        """
        logger.info(f"🚨 Sending emergency shutdown notification")

        response = await self.client.post(
            "/api/v1/notifications",
            json_data={
                "user_id": user_id,
                "type": "EMERGENCY_SHUTDOWN",
                "title": "🚨 Auto-Trading Emergency Shutdown",
                "message": f"Auto-trading stopped: {reason}. Total loss: ${total_loss:.2f}",
                "priority": "HIGH",
                "data": {
                    "reason": reason,
                    "total_loss": total_loss
                }
            }
        )

        if response:
            logger.info("✅ Emergency shutdown notification sent")
            return True
        else:
            logger.error("❌ Failed to send emergency shutdown notification")
            return False

    async def close(self):
        """Close client."""
        await self.client.close()
