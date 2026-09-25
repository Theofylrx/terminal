"""Alpaca connector for stock market data."""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional

import websockets
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from .base import Bar, BrokerConnector, MarketDataType, Quote, Trade


logger = logging.getLogger(__name__)


class AlpacaConnector(BrokerConnector):
    """
    Alpaca connector for real-time and historical stock market data.

    Provides access to US stock markets through Alpaca's WebSocket
    and REST APIs.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        data_url: str = "https://data.alpaca.markets",
        ws_url: str = "wss://stream.data.alpaca.markets/v2/iex",
    ):
        """
        Initialize Alpaca connector.

        Args:
            api_key: Alpaca API key.
            api_secret: Alpaca API secret.
            data_url: Base URL for data API.
            ws_url: WebSocket URL for streaming data.
        """
        super().__init__("alpaca")
        self.api_key = api_key
        self.api_secret = api_secret
        self.data_url = data_url
        self.ws_url = ws_url

        # Initialize REST client for historical data
        self.historical_client = StockHistoricalDataClient(api_key, api_secret)

        # WebSocket connection
        self.ws_connection = None
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish WebSocket connection to Alpaca."""
        try:
            self.logger.info(f"Connecting to Alpaca WebSocket at {self.ws_url}")

            self.ws_connection = await websockets.connect(self.ws_url)
            self.connected = True

            # Authenticate
            auth_message = {
                "action": "auth",
                "key": self.api_key,
                "secret": self.api_secret,
            }
            await self.ws_connection.send(json.dumps(auth_message))

            # Wait for auth response
            response = await self.ws_connection.recv()
            auth_response = json.loads(response)

            if auth_response[0].get("T") == "error":
                raise ConnectionError(f"Alpaca auth failed: {auth_response}")

            self.logger.info("Alpaca WebSocket authenticated successfully")

            # Start listening for messages
            self._listen_task = asyncio.create_task(self._listen())

        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Alpaca: {e}")
            raise ConnectionError(f"Alpaca connection failed: {e}")

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self.logger.info("Disconnecting from Alpaca")

        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self.ws_connection:
            await self.ws_connection.close()

        self.connected = False
        self.subscribed_symbols.clear()
        self.logger.info("Alpaca disconnected")

    async def subscribe(
        self,
        symbols: List[str],
        data_types: Optional[List[MarketDataType]] = None
    ) -> None:
        """
        Subscribe to market data for symbols.

        Args:
            symbols: List of stock symbols (e.g., ["AAPL", "GOOGL"]).
            data_types: Types to subscribe to (trades, quotes, bars).
        """
        if not self.connected:
            raise ConnectionError("Not connected to Alpaca")

        if data_types is None:
            data_types = [MarketDataType.TRADE, MarketDataType.QUOTE, MarketDataType.BAR]

        # Build subscription message
        subscribe_msg = {"action": "subscribe"}

        for data_type in data_types:
            if data_type == MarketDataType.TRADE:
                subscribe_msg["trades"] = symbols
            elif data_type == MarketDataType.QUOTE:
                subscribe_msg["quotes"] = symbols
            elif data_type == MarketDataType.BAR:
                subscribe_msg["bars"] = symbols

        await self.ws_connection.send(json.dumps(subscribe_msg))

        # Update subscribed symbols
        self.subscribed_symbols.update(symbols)

        self.logger.info(f"Subscribed to {len(symbols)} symbols: {symbols}")

    async def unsubscribe(self, symbols: List[str]) -> None:
        """Unsubscribe from symbols."""
        if not self.connected:
            return

        unsubscribe_msg = {
            "action": "unsubscribe",
            "trades": symbols,
            "quotes": symbols,
            "bars": symbols,
        }

        await self.ws_connection.send(json.dumps(unsubscribe_msg))

        # Remove from subscribed set
        self.subscribed_symbols.difference_update(symbols)

        self.logger.info(f"Unsubscribed from {len(symbols)} symbols")

    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars from Alpaca.

        Args:
            symbol: Stock symbol.
            timeframe: Bar size (1Min, 5Min, 15Min, 1Hour, 1Day).
            start: Start datetime.
            end: End datetime.
            limit: Max bars to return.

        Returns:
            List of Bar objects.
        """
        try:
            # Map timeframe string to Alpaca TimeFrame
            tf_map = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame(5, "Min"),
                "15m": TimeFrame(15, "Min"),
                "30m": TimeFrame(30, "Min"),
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day,
            }

            alpaca_timeframe = tf_map.get(timeframe.lower(), TimeFrame.Minute)

            request_params = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=alpaca_timeframe,
                start=start,
                end=end,
                limit=limit,
            )

            bars_data = self.historical_client.get_stock_bars(request_params)

            # Convert to our Bar model
            bars = []
            if symbol in bars_data:
                for bar in bars_data[symbol]:
                    bars.append(
                        Bar(
                            symbol=symbol,
                            timeframe=timeframe,
                            open=float(bar.open),
                            high=float(bar.high),
                            low=float(bar.low),
                            close=float(bar.close),
                            volume=float(bar.volume),
                            timestamp=bar.timestamp,
                            trade_count=bar.trade_count,
                            vwap=float(bar.vwap) if bar.vwap else None,
                        )
                    )

            self.logger.debug(f"Fetched {len(bars)} historical bars for {symbol}")
            return bars

        except Exception as e:
            self.logger.error(f"Failed to fetch historical bars: {e}")
            return []

    async def get_latest_quote(self, symbol: str) -> Optional[Quote]:
        """
        Get latest quote (bid/ask) for a symbol from Alpaca.

        Args:
            symbol: Stock symbol (e.g., "AAPL").

        Returns:
            Quote object with latest bid/ask prices, or None if failed.
        """
        try:
            # Use the Alpaca SDK to get latest quote
            from alpaca.data.requests import StockLatestQuoteRequest
            from alpaca.data.historical import StockHistoricalDataClient

            # Create a quote request
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)

            # Get latest quote
            quote_data = self.historical_client.get_stock_latest_quote(request)

            if symbol in quote_data:
                latest = quote_data[symbol]
                quote = Quote(
                    symbol=symbol,
                    bid_price=float(latest.bid_price),
                    bid_size=float(latest.bid_size),
                    ask_price=float(latest.ask_price),
                    ask_size=float(latest.ask_size),
                    timestamp=latest.timestamp,
                )

                self.logger.debug(f"Fetched latest quote for {symbol}: bid={quote.bid_price}, ask={quote.ask_price}")
                return quote
            else:
                self.logger.warning(f"No quote data returned for {symbol}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to fetch latest quote for {symbol}: {e}")
            return None

    async def _listen(self) -> None:
        """Listen for incoming WebSocket messages."""
        try:
            async for message in self.ws_connection:
                try:
                    data = json.loads(message)
                    await self._process_messages(data)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    self.logger.error(f"Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            self.logger.warning("Alpaca WebSocket connection closed")
            await self._handle_disconnect()

        except Exception as e:
            self.logger.error(f"Error in WebSocket listener: {e}")
            await self._handle_disconnect()

    async def _process_messages(self, messages: List[dict]) -> None:
        """Process incoming messages from Alpaca."""
        for msg in messages:
            msg_type = msg.get("T")

            # Trade message
            if msg_type == "t":
                trade = Trade(
                    symbol=msg["S"],
                    price=float(msg["p"]),
                    size=float(msg["s"]),
                    timestamp=datetime.fromisoformat(msg["t"].replace("Z", "+00:00")),
                    exchange=msg.get("x"),
                    conditions=msg.get("c"),
                )
                await self._emit(MarketDataType.TRADE, trade)

            # Quote message
            elif msg_type == "q":
                quote = Quote(
                    symbol=msg["S"],
                    bid_price=float(msg["bp"]),
                    bid_size=float(msg["bs"]),
                    ask_price=float(msg["ap"]),
                    ask_size=float(msg["as"]),
                    timestamp=datetime.fromisoformat(msg["t"].replace("Z", "+00:00")),
                    exchange=msg.get("x"),
                )
                await self._emit(MarketDataType.QUOTE, quote)

            # Bar message (1-minute)
            elif msg_type == "b":
                bar = Bar(
                    symbol=msg["S"],
                    timeframe="1m",
                    open=float(msg["o"]),
                    high=float(msg["h"]),
                    low=float(msg["l"]),
                    close=float(msg["c"]),
                    volume=float(msg["v"]),
                    timestamp=datetime.fromisoformat(msg["t"].replace("Z", "+00:00")),
                    trade_count=msg.get("n"),
                    vwap=float(msg["vw"]) if msg.get("vw") else None,
                )
                await self._emit(MarketDataType.BAR, bar)

            # Subscription confirmation
            elif msg_type == "subscription":
                self.logger.debug(f"Subscription confirmed: {msg}")

            # Error message
            elif msg_type == "error":
                self.logger.error(f"Alpaca error: {msg.get('msg')}")
