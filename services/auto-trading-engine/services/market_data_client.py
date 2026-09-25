"""
Market Data Service Client
Calls Market Data Service for quotes and historical data
"""

import logging
from typing import Optional, Dict, Any

from .http_client import HTTPClient
from ..core.config import settings

logger = logging.getLogger("auto-trading-engine.market_data_client")


class MarketDataClient:
    """Client for Market Data Service."""

    def __init__(self):
        """Initialize Market Data client."""
        self.client = HTTPClient(
            base_url=settings.MARKET_DATA_SERVICE_URL,
            service_name="MarketDataService"
        )

    async def get_latest_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get latest quote for a symbol.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTCUSDT")

        Returns:
            Quote data if successful:
            {
                "symbol": "AAPL",
                "close": 152.50,  # Latest price
                "open": 151.80,
                "high": 153.20,
                "low": 151.50,
                "volume": 1234567,
                "timestamp": "2024-01-20T14:30:00Z"
            }
        """
        logger.debug(f"📊 Getting latest quote for {symbol}")

        # Use /latest endpoint with default 1m timeframe
        response = await self.client.get(f"/api/v1/latest/{symbol}", params={"timeframe": "1m"})

        if response:
            # Map response to have 'price' field for backward compatibility
            if 'close' in response:
                response['price'] = response['close']
            logger.debug(f"✅ Quote received for {symbol}: ${response.get('price')}")
            return response
        else:
            logger.warning(f"⚠️  Failed to get quote for {symbol}")
            return None

    async def get_historical_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        limit: int = 100
    ) -> Optional[Dict[str, Any]]:
        """
        Get historical OHLCV data.

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of bars to retrieve

        Returns:
            Historical data if successful
        """
        logger.debug(f"📊 Getting historical data for {symbol} ({timeframe})")

        response = await self.client.get(
            f"/api/v1/ohlcv/{symbol}",
            params={"timeframe": timeframe, "limit": limit}
        )

        if response:
            logger.debug(f"✅ Historical data received for {symbol}")
            return response
        else:
            logger.warning(f"⚠️  Failed to get historical data for {symbol}")
            return None

    async def close(self):
        """Close client."""
        await self.client.close()
