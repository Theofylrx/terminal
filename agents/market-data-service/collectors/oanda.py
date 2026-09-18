"""OANDA connector for forex market data."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp
from oandapyV20 import API
from oandapyV20.endpoints import instruments

from .base import Bar, BrokerConnector, MarketDataType, Quote


logger = logging.getLogger(__name__)


class OandaConnector(BrokerConnector):
    """
    OANDA connector for real-time and historical forex data.

    Provides access to major forex pairs, commodities, and indices.
    """

    def __init__(
        self,
        api_key: str,
        account_id: str,
        base_url: str = "https://api-fxpractice.oanda.com",
        stream_url: str = "https://stream-fxpractice.oanda.com",
    ):
        """
        Initialize OANDA connector.

        Args:
            api_key: OANDA API key.
            account_id: OANDA account ID.
            base_url: Base URL for REST API.
            stream_url: Base URL for streaming API.
        """
        super().__init__("oanda")
        self.api_key = api_key
        self.account_id = account_id
        self.base_url = base_url
        self.stream_url = stream_url

        # REST client for historical data
        self.api = API(access_token=api_key, environment="practice")

        # Streaming connection
        self.stream_session: Optional[aiohttp.ClientSession] = None
        self.stream_response: Optional[aiohttp.ClientResponse] = None
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Initialize OANDA connection."""
        try:
            self.logger.info("Connecting to OANDA")

            # Create aiohttp session for streaming
            self.stream_session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

            self.connected = True
            self.logger.info("OANDA client initialized successfully")

        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to OANDA: {e}")
            raise ConnectionError(f"OANDA connection failed: {e}")

    async def disconnect(self) -> None:
        """Close OANDA connection."""
        self.logger.info("Disconnecting from OANDA")

        # Cancel listening task
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        # Close stream response
        if self.stream_response:
            self.stream_response.close()

        # Close session
        if self.stream_session:
            await self.stream_session.close()

        self.connected = False
        self.subscribed_symbols.clear()
        self.logger.info("OANDA disconnected")

    async def subscribe(
        self,
        symbols: List[str],
        data_types: Optional[List[MarketDataType]] = None
    ) -> None:
        """
        Subscribe to forex pricing stream.

        Args:
            symbols: List of instruments (e.g., ["EUR_USD", "GBP_USD"]).
            data_types: Currently only QUOTE is supported for streaming.
        """
        if not self.connected:
            raise ConnectionError("Not connected to OANDA")

        # Add new symbols to subscription
        self.subscribed_symbols.update(symbols)

        # Restart stream with all symbols
        await self._start_pricing_stream()

        self.logger.info(f"Subscribed to {len(symbols)} forex pairs: {symbols}")

    async def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe from symbols."""
        if not self.subscribed_symbols:
            return

        # Remove symbols
        self.subscribed_symbols.difference_update(symbols)

        # Restart stream if symbols remain
        if self.subscribed_symbols:
            await self._start_pricing_stream()
        else:
            # Stop stream if no symbols
            if self._listen_task:
                self._listen_task.cancel()
            if self.stream_response:
                self.stream_response.close()

        self.logger.info(f"Unsubscribed from {len(symbols)} forex pairs")

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """
        Fetch historical candlestick data from OANDA.

        Args:
            symbol: Instrument (e.g., "EUR_USD").
            timeframe: Granularity (M1, M5, M15, H1, H4, D).
            start: Start datetime.
            end: End datetime.
            limit: Max candles to return (max 5000).

        Returns:
            List of Bar objects.
        """
        try:
            # Map timeframe to OANDA granularity
            granularity_map = {
                "1m": "M1",
                "5m": "M5",
                "15m": "M15",
                "30m": "M30",
                "1h": "H1",
                "4h": "H4",
                "1d": "D",
            }

            granularity = granularity_map.get(timeframe.lower(), "M1")

            # Build request parameters
            params = {
                "from": start.isoformat() + "Z",
                "to": end.isoformat() + "Z",
                "granularity": granularity,
                "price": "M",  # Midpoint prices
            }

            if limit:
                params["count"] = min(limit, 5000)

            # Fetch candles
            request = instruments.InstrumentsCandles(instrument=symbol, params=params)
            response = self.api.request(request)

            # Convert to Bar objects
            bars = []
            for candle in response.get("candles", []):
                if candle.get("complete"):
                    mid = candle["mid"]
                    bars.append(
                        Bar(
                            symbol=symbol,
                            timeframe=timeframe,
                            open=float(mid["o"]),
                            high=float(mid["h"]),
                            low=float(mid["l"]),
                            close=float(mid["c"]),
                            volume=float(candle.get("volume", 0)),
                            timestamp=datetime.fromisoformat(
                                candle["time"].replace("Z", "+00:00")
                            ),
                        )
                    )

            self.logger.debug(f"Fetched {len(bars)} historical bars for {symbol}")
            return bars

        except Exception as e:
            self.logger.error(f"Failed to fetch historical bars: {e}")
            return []

    async def _start_pricing_stream(self) -> None:
        """Start or restart the pricing stream with current symbols."""
        # Cancel existing stream
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self.stream_response:
            self.stream_response.close()

        if not self.subscribed_symbols:
            return

        # Build stream URL
        instruments_param = ",".join(self.subscribed_symbols)
        stream_url = (
            f"{self.stream_url}/v3/accounts/{self.account_id}/pricing/stream"
            f"?instruments={instruments_param}"
        )

        try:
            # Start new stream
            self.stream_response = await self.stream_session.get(stream_url)

            # Start listening task
            self._listen_task = asyncio.create_task(self._listen())

            self.logger.info(f"Started pricing stream for {len(self.subscribed_symbols)} instruments")

        except Exception as e:
            self.logger.error(f"Failed to start pricing stream: {e}")
            await self._handle_disconnect()

    async def _listen(self) -> None:
        """Listen for incoming pricing stream."""
        try:
            async for line in self.stream_response.content:
                try:
                    if not line:
                        continue

                    data = json.loads(line.decode("utf-8"))
                    await self._process_message(data)

                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            self.logger.debug("Pricing stream listener cancelled")

        except Exception as e:
            self.logger.error(f"Error in pricing stream: {e}")
            await self._handle_disconnect()

    async def _process_message(self, data: dict) -> None:
        """Process incoming pricing message."""
        msg_type = data.get("type")

        # Price update
        if msg_type == "PRICE":
            instrument = data.get("instrument")

            # Extract bid/ask
            bids = data.get("bids", [{}])
            asks = data.get("asks", [{}])

            if bids and asks:
                quote = Quote(
                    symbol=instrument,
                    bid_price=float(bids[0].get("price", 0)),
                    bid_size=float(bids[0].get("liquidity", 0)),
                    ask_price=float(asks[0].get("price", 0)),
                    ask_size=float(asks[0].get("liquidity", 0)),
                    timestamp=datetime.fromisoformat(
                        data["time"].replace("Z", "+00:00")
                    ),
                )
                await self._emit(MarketDataType.QUOTE, quote)

        # Heartbeat
        elif msg_type == "HEARTBEAT":
            self.logger.debug("Received heartbeat from OANDA")
