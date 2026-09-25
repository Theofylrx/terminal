"""
Technical Analyst Service Client
Calls Technical Analyst Service for pattern detection and analysis
"""

import logging
from typing import Optional, Dict, Any, List

from .http_client import HTTPClient
from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.technical_analyst_client")


class TechnicalAnalystClient:
    """Client for Technical Analyst Service."""

    def __init__(self):
        """Initialize Technical Analyst client."""
        self.client = HTTPClient(
            base_url=settings.TECHNICAL_ANALYST_SERVICE_URL,
            service_name="TechnicalAnalystService"
        )

    async def analyze(
        self,
        symbol: str,
        timeframes: Optional[List[str]] = None,
        include_reasoning: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get technical analysis for a symbol.

        Args:
            symbol: Trading symbol
            timeframes: List of timeframes to analyze (e.g., ["5m", "15m", "1h"])
            include_reasoning: Include AI reasoning in response

        Returns:
            Analysis data if successful:
            {
                "symbol": "AAPL",
                "direction": "BULLISH",
                "confidence": 82.5,
                "patterns": [
                    {
                        "type": "ORDER_BLOCK",
                        "timeframe": "15m",
                        "confidence": 88.0,
                        "level": 150.00
                    },
                    ...
                ],
                "indicators": {
                    "rsi": 68.3,
                    "macd": "BULLISH",
                    "moving_averages": "BULLISH"
                },
                "support_levels": [150.00, 148.20, 145.50],
                "resistance_levels": [153.80, 155.50, 158.00],
                "reasoning": "Strong bullish structure detected..."
            }
        """
        if timeframes is None:
            timeframes = ["5m", "15m", "1h"]

        logger.debug(f"🔍 Analyzing {symbol} on {timeframes}")

        response = await self.client.post(
            "/api/v1/analyze",
            json_data={
                "symbol": symbol,
                "timeframes": timeframes,
                "include_reasoning": include_reasoning
            }
        )

        if response:
            logger.info(
                f"✅ Analysis for {symbol}: {response.get('direction')} "
                f"({response.get('confidence')}% confidence)"
            )
            return response
        else:
            logger.warning(f"⚠️  Failed to analyze {symbol}")
            return None

    async def get_entry_signal(
        self,
        symbol: str,
        current_price: float
    ) -> Optional[Dict[str, Any]]:
        """
        Get entry signal recommendation.

        Args:
            symbol: Trading symbol
            current_price: Current market price

        Returns:
            Entry signal if available
        """
        logger.debug(f"🎯 Getting entry signal for {symbol} at ${current_price}")

        response = await self.client.post(
            "/api/v1/signals/entry",
            json_data={
                "symbol": symbol,
                "current_price": current_price
            }
        )

        if response and response.get('has_signal'):
            logger.info(f"✅ Entry signal for {symbol}: {response.get('direction')}")
            return response
        else:
            logger.debug(f"ℹ️  No entry signal for {symbol}")
            return None

    async def close(self):
        """Close client."""
        await self.client.close()
