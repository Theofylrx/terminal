"""Binance connector for cryptocurrency market data."""

import asyncio
import json
import logging
from datetime import datetime
from typing import List, Optional

import websockets
from binance import AsyncClient
from binance.enums import *

from .base import Bar, BrokerConnector, MarketDataType, Trade


logger = logging.getLogger(__name__)


class BinanceConnector(BrokerConnector):
    """
    Binance connector for real-time and historical cryptocurrency data.

    Supports spot and futures markets on Binance.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: bool = True,
    ):
        """
        Initialize Binance connector.

        Args:
            api_key: Binance API key (optional for public data).
            api_secret: Binance API secret.
            testnet: Use testnet instead of production.
        """
        super().__init__("binance")
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

        # REST client for historical data
        self.client: Optional[AsyncClient] = None

        # WebSocket connections (one per symbol)
        self.ws_connections: dict = {}
        self._listen_tasks: dict = {}

    async def connect(self) -> None:
        """Initialize Binance async client."""
        try:
            self.logger.info("Connecting to Binance")

            if self.testnet:
                self.client = await AsyncClient.create(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                    testnet=True,
                )
            else:
                self.client = await AsyncClient.create(
                    api_key=self.api_key,
                    api_secret=self.api_secret,
                )

            self.connected = True
            self.logger.info("Binance client initialized successfully")

        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Binance: {e}")
            raise ConnectionError(f"Binance connection failed: {e}")

    async def disconnect(self) -> None:
        """Close all connections."""
        self.logger.info("Disconnecting from Binance")

        # Cancel all listening tasks
        for task in self._listen_tasks.values():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Close all WebSocket connections
        for ws in self.ws_connections.values():
            await ws.close()

        # Close REST client
        if self.client:
            await self.client.close_connection()

        self.connected = False
        self.subscribed_symbols.clear()
        self.ws_connections.clear()
        self._listen_tasks.clear()
        self.logger.info("Binance disconnected")

    async def subscribe(
        self,
        symbols: List[str],
        data_types: Optional[List[MarketDataType]] = None
    ) -> None:
        """
        Subscribe to market data for symbols.

        Args:
            symbols: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"]).
            data_types: Types to subscribe to (trades, bars).
        """
        if not self.connected:
            raise ConnectionError("Not connected to Binance")

        if data_types is None:
            data_types = [MarketDataType.TRADE, MarketDataType.BAR]

        for symbol in symbols:
            if symbol in self.subscribed_symbols:
                self.logger.debug(f"Already subscribed to {symbol}")
                continue

            # Create WebSocket streams for this symbol
            streams = []
            symbol_lower = symbol.lower()

            if MarketDataType.TRADE in data_types:
                streams.append(f"{symbol_lower}@trade")

            if MarketDataType.BAR in data_types:
                streams.append(f"{symbol_lower}@kline_1m")

            # Binance WebSocket URL
            stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"

            if self.testnet:
                stream_url = f"wss://testnet.binance.vision/stream?streams={'/'.join(streams)}"

            try:
                ws = await websockets.connect(stream_url)
                self.ws_connections[symbol] = ws

                # Start listening task for this symbol
                listen_task = asyncio.create_task(self._listen(symbol, ws))
                self._listen_tasks[symbol] = listen_task

                self.subscribed_symbols.add(symbol)
                self.logger.info(f"Subscribed to {symbol}")

            except Exception as e:
                self.logger.error(f"Failed to subscribe to {symbol}: {e}")

    async def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe from symbols."""
        for symbol in symbols:
            if symbol not in self.subscribed_symbols:
                continue

            # Cancel listening task
            if symbol in self._listen_tasks:
                self._listen_tasks[symbol].cancel()
                try:
                    await self._listen_tasks[symbol]
                except asyncio.CancelledError:
                    pass
                del self._listen_tasks[symbol]

            # Close WebSocket
            if symbol in self.ws_connections:
                await self.ws_connections[symbol].close()
                del self.ws_connections[symbol]

            self.subscribed_symbols.discard(symbol)
            self.logger.info(f"Unsubscribed from {symbol}")

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """
        Fetch historical klines (candlesticks) from Binance.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT").
            timeframe: Interval (1m, 5m, 15m, 1h, 4h, 1d).
            start: Start datetime.
            end: End datetime.
            limit: Max bars to return (max 1000).

        Returns:
            List of Bar objects.
        """
        if not self.client:
            raise ConnectionError("Not connected to Binance")

        try:
            # Map timeframe to Binance interval
            interval_map = {
                "1m": KLINE_INTERVAL_1MINUTE,
                "5m": KLINE_INTERVAL_5MINUTE,
                "15m": KLINE_INTERVAL_15MINUTE,
                "30m": KLINE_INTERVAL_30MINUTE,
                "1h": KLINE_INTERVAL_1HOUR,
                "4h": KLINE_INTERVAL_4HOUR,
                "1d": KLINE_INTERVAL_1DAY,
            }

            interval = interval_map.get(timeframe.lower(), KLINE_INTERVAL_1MINUTE)

            # Fetch klines
            klines = await self.client.get_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=int(start.timestamp() * 1000),
                end_str=int(end.timestamp() * 1000),
                limit=limit or 1000,
            )

            # Convert to Bar objects
            bars = []
            for kline in klines:
                bars.append(
                    Bar(
                        symbol=symbol,
                        timeframe=timeframe,
                        open=float(kline[1]),
                        high=float(kline[2]),
                        low=float(kline[3]),
                        close=float(kline[4]),
                        volume=float(kline[5]),
                        timestamp=datetime.fromtimestamp(kline[0] / 1000),
                        trade_count=int(kline[8]),
                    )
                )

            self.logger.debug(f"Fetched {len(bars)} historical bars for {symbol}")
            return bars

        except Exception as e:
            self.logger.error(f"Failed to fetch historical bars: {e}")
            return []

    async def _listen(self, symbol: str, ws) -> None:
        """Listen for incoming WebSocket messages for a symbol."""
        try:
            async for message in ws:
                try:
                    data = json.loads(message)
                    await self._process_message(symbol, data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning(f"Binance WebSocket for {symbol} closed")
            # Attempt to reconnect
            if symbol in self.subscribed_symbols:
                await self._reconnect_symbol(symbol)

        except Exception as e:
            self.logger.error(f"Error in WebSocket listener for {symbol}: {e}")

    async def _reconnect_symbol(self, symbol: str) -> None:
        """Reconnect WebSocket for a specific symbol."""
        self.logger.info(f"Reconnecting {symbol}")
        try:
            await self.unsubscribe([symbol])
            await asyncio.sleep(1)
            await self.subscribe([symbol])
        except Exception as e:
            self.logger.error(f"Failed to reconnect {symbol}: {e}")

    async def _process_message(self, symbol: str, data: dict) -> None:
        """Process incoming message from Binance."""
        if "stream" not in data:
            return

        stream_type = data["stream"].split("@")[1]
        msg_data = data.get("data", {})

        # Trade message
        if stream_type == "trade":
            trade = Trade(
                symbol=msg_data["s"],
                price=float(msg_data["p"]),
                size=float(msg_data["q"]),
                timestamp=datetime.fromtimestamp(msg_data["T"] / 1000),
            )
            await self._emit(MarketDataType.TRADE, trade)

        # Kline (candlestick) message
        elif stream_type.startswith("kline"):
            kline = msg_data.get("k", {})
            if kline.get("x"):  # Only emit closed candles
                bar = Bar(
                    symbol=kline["s"],
                    timeframe="1m",
                    open=float(kline["o"]),
                    high=float(kline["h"]),
                    low=float(kline["l"]),
                    close=float(kline["c"]),
                    volume=float(kline["v"]),
                    timestamp=datetime.fromtimestamp(kline["t"] / 1000),
                    trade_count=int(kline["n"]),
                )
                await self._emit(MarketDataType.BAR, bar)
