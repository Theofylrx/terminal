"""Market Data Service - Orchestrates data collection and distribution."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession

from ..collectors import AlpacaConnector, BinanceConnector, OandaConnector, MarketDataType
from ..collectors.base import Bar, Quote, Trade
from ..repositories import OHLCVRepository, QuoteRepository, TradeRepository
from ..core.config import settings

# Import event publisher from shared
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from shared.events.event_bus import EventPublisher
from shared.events.event_types import EventType


logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Market Data Service orchestrates data collection from multiple brokers,
    stores data in TimescaleDB, and distributes updates via events.
    """

    def __init__(
        self,
        session: AsyncSession,
        event_publisher: Optional[EventPublisher] = None,
    ):
        """
        Initialize Market Data Service.

        Args:
            session: Database session for repositories.
            event_publisher: Event publisher for distributing updates.
        """
        self.session = session
        self.event_publisher = event_publisher

        # Repositories
        self.ohlcv_repo = OHLCVRepository(session)
        self.quote_repo = QuoteRepository(session)
        self.trade_repo = TradeRepository(session)

        # Broker connectors
        self.connectors: Dict[str, any] = {}
        self._initialize_connectors()

        # Track subscriptions
        self.subscribed_symbols: Dict[str, Set[str]] = {
            "alpaca": set(),
            "binance": set(),
            "oanda": set(),
        }

        # Client WebSocket connections (for real-time distribution)
        self.websocket_clients: Set = set()

        logger.info("MarketDataService initialized")

    def _initialize_connectors(self):
        """Initialize broker connectors based on configuration."""
        # Alpaca (stocks)
        if settings.ENABLE_ALPACA and settings.ALPACA_API_KEY:
            try:
                self.connectors["alpaca"] = AlpacaConnector(
                    api_key=settings.ALPACA_API_KEY,
                    api_secret=settings.ALPACA_API_SECRET,
                    data_url=settings.ALPACA_DATA_URL,
                    ws_url=settings.ALPACA_WS_URL,
                )

                # Register callbacks
                self.connectors["alpaca"].register_callback(
                    MarketDataType.TRADE, self._handle_trade
                )
                self.connectors["alpaca"].register_callback(
                    MarketDataType.QUOTE, self._handle_quote
                )
                self.connectors["alpaca"].register_callback(
                    MarketDataType.BAR, self._handle_bar
                )

                logger.info("Alpaca connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca connector: {e}")

        # Binance (crypto)
        if settings.ENABLE_BINANCE:
            try:
                self.connectors["binance"] = BinanceConnector(
                    api_key=settings.BINANCE_API_KEY,
                    api_secret=settings.BINANCE_API_SECRET,
                    testnet=settings.BINANCE_TESTNET,
                )

                # Register callbacks
                self.connectors["binance"].register_callback(
                    MarketDataType.TRADE, self._handle_trade
                )
                self.connectors["binance"].register_callback(
                    MarketDataType.BAR, self._handle_bar
                )

                logger.info("Binance connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Binance connector: {e}")

        # OANDA (forex)
        if settings.ENABLE_OANDA and settings.OANDA_API_KEY:
            try:
                self.connectors["oanda"] = OandaConnector(
                    api_key=settings.OANDA_API_KEY,
                    account_id=settings.OANDA_ACCOUNT_ID,
                    base_url=settings.OANDA_BASE_URL,
                    stream_url=settings.OANDA_STREAM_URL,
                )

                # Register callbacks
                self.connectors["oanda"].register_callback(
                    MarketDataType.QUOTE, self._handle_quote
                )

                logger.info("OANDA connector initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OANDA connector: {e}")

    async def start(self):
        """Start all connectors and subscribe to default symbols."""
        logger.info("Starting Market Data Service")

        # Connect all brokers
        for name, connector in self.connectors.items():
            try:
                await connector.connect()
                logger.info(f"{name} connected")
            except Exception as e:
                logger.error(f"Failed to connect {name}: {e}")

        # Subscribe to default symbols
        await self._subscribe_defaults()

        logger.info("Market Data Service started")

    async def stop(self):
        """Stop all connectors."""
        logger.info("Stopping Market Data Service")

        for name, connector in self.connectors.items():
            try:
                await connector.disconnect()
                logger.info(f"{name} disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting {name}: {e}")

        logger.info("Market Data Service stopped")

    async def _subscribe_defaults(self):
        """Subscribe to default symbols from configuration."""
        if "alpaca" in self.connectors and settings.DEFAULT_STOCK_SYMBOLS:
            await self.subscribe_symbols("alpaca", settings.DEFAULT_STOCK_SYMBOLS)

        if "binance" in self.connectors and settings.DEFAULT_CRYPTO_SYMBOLS:
            await self.subscribe_symbols("binance", settings.DEFAULT_CRYPTO_SYMBOLS)

        if "oanda" in self.connectors and settings.DEFAULT_FOREX_SYMBOLS:
            await self.subscribe_symbols("oanda", settings.DEFAULT_FOREX_SYMBOLS)

    async def subscribe_symbols(self, broker: str, symbols: List[str]):
        """
        Subscribe to symbols on a specific broker.

        Args:
            broker: Broker name (alpaca, binance, oanda).
            symbols: List of symbols to subscribe to.
        """
        if broker not in self.connectors:
            raise ValueError(f"Unknown broker: {broker}")

        connector = self.connectors[broker]

        try:
            await connector.subscribe(symbols)
            self.subscribed_symbols[broker].update(symbols)
            logger.info(f"Subscribed to {len(symbols)} symbols on {broker}")
        except Exception as e:
            logger.error(f"Failed to subscribe on {broker}: {e}")
            raise

    async def unsubscribe_symbols(self, broker: str, symbols: List[str]):
        """Unsubscribe from symbols on a specific broker."""
        if broker not in self.connectors:
            raise ValueError(f"Unknown broker: {broker}")

        connector = self.connectors[broker]

        try:
            await connector.unsubscribe(symbols)
            self.subscribed_symbols[broker].difference_update(symbols)
            logger.info(f"Unsubscribed from {len(symbols)} symbols on {broker}")
        except Exception as e:
            logger.error(f"Failed to unsubscribe on {broker}: {e}")
            raise

    async def get_historical_bars(
        self,
        broker: str,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """Fetch historical bars from broker and store in database."""
        if broker not in self.connectors:
            raise ValueError(f"Unknown broker: {broker}")

        connector = self.connectors[broker]

        try:
            bars = await connector.get_historical_bars(
                symbol, timeframe, start, end, limit
            )

            # Store in database
            for bar in bars:
                await self.ohlcv_repo.upsert(
                    symbol=bar.symbol,
                    timeframe=bar.timeframe,
                    timestamp=bar.timestamp,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                    source=broker,
                    quote_volume=None,
                    num_trades=bar.trade_count,
                )

            logger.info(f"Stored {len(bars)} historical bars for {symbol}")
            return bars

        except Exception as e:
            logger.error(f"Failed to fetch historical bars: {e}")
            raise

    # Data handlers (callbacks from brokers)

    async def _handle_trade(self, trade: Trade):
        """Handle incoming trade data."""
        try:
            # Store in database
            await self.trade_repo.upsert(
                symbol=trade.symbol,
                timestamp=trade.timestamp,
                trade_id=f"{trade.timestamp.timestamp()}_{trade.price}",  # Generate ID
                price=trade.price,
                size=trade.size,
                source=trade.exchange or "unknown",
                exchange=trade.exchange,
            )

            # Publish event
            if self.event_publisher:
                await self.event_publisher.publish(
                    EventType.MARKET_DATA_TRADE.value,
                    {
                        "symbol": trade.symbol,
                        "price": trade.price,
                        "size": trade.size,
                        "timestamp": trade.timestamp.isoformat(),
                    },
                )

            # Send to WebSocket clients
            await self._broadcast_to_clients({
                "type": "trade",
                "data": {
                    "symbol": trade.symbol,
                    "price": trade.price,
                    "size": trade.size,
                    "timestamp": trade.timestamp.isoformat(),
                }
            })

        except Exception as e:
            logger.error(f"Error handling trade: {e}")

    async def _handle_quote(self, quote: Quote):
        """Handle incoming quote data."""
        try:
            # Store in database
            await self.quote_repo.upsert(
                symbol=quote.symbol,
                timestamp=quote.timestamp,
                bid_price=quote.bid_price,
                bid_size=quote.bid_size,
                ask_price=quote.ask_price,
                ask_size=quote.ask_size,
                source=quote.exchange or "unknown",
                exchange=quote.exchange,
            )

            # Publish event
            if self.event_publisher:
                await self.event_publisher.publish(
                    EventType.MARKET_DATA_QUOTE.value,
                    {
                        "symbol": quote.symbol,
                        "bid": quote.bid_price,
                        "ask": quote.ask_price,
                        "timestamp": quote.timestamp.isoformat(),
                    },
                )

            # Send to WebSocket clients
            await self._broadcast_to_clients({
                "type": "quote",
                "data": {
                    "symbol": quote.symbol,
                    "bid": quote.bid_price,
                    "ask": quote.ask_price,
                    "timestamp": quote.timestamp.isoformat(),
                }
            })

        except Exception as e:
            logger.error(f"Error handling quote: {e}")

    async def _handle_bar(self, bar: Bar):
        """Handle incoming bar (candlestick) data."""
        try:
            # Store in database
            await self.ohlcv_repo.upsert(
                symbol=bar.symbol,
                timeframe=bar.timeframe,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source="live",
                num_trades=bar.trade_count,
            )

            # Publish event
            if self.event_publisher:
                await self.event_publisher.publish(
                    EventType.MARKET_DATA_BAR.value,
                    {
                        "symbol": bar.symbol,
                        "timeframe": bar.timeframe,
                        "close": bar.close,
                        "volume": bar.volume,
                        "timestamp": bar.timestamp.isoformat(),
                    },
                )

            # Send to WebSocket clients
            await self._broadcast_to_clients({
                "type": "bar",
                "data": {
                    "symbol": bar.symbol,
                    "timeframe": bar.timeframe,
                    "open": bar.open,
                    "high": bar.high,
                    "low": bar.low,
                    "close": bar.close,
                    "volume": bar.volume,
                    "timestamp": bar.timestamp.isoformat(),
                }
            })

        except Exception as e:
            logger.error(f"Error handling bar: {e}")

    async def _broadcast_to_clients(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        if not self.websocket_clients:
            return

        # Send to all clients (implementation depends on WebSocket library)
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send_json(message)
            except Exception:
                disconnected.add(client)

        # Remove disconnected clients
        self.websocket_clients.difference_update(disconnected)

    def add_websocket_client(self, client):
        """Add a WebSocket client for real-time updates."""
        self.websocket_clients.add(client)
        logger.info(f"WebSocket client connected. Total: {len(self.websocket_clients)}")

    def remove_websocket_client(self, client):
        """Remove a WebSocket client."""
        self.websocket_clients.discard(client)
        logger.info(f"WebSocket client disconnected. Total: {len(self.websocket_clients)}")

    async def get_live_price(self, symbol: str) -> float:
        """
        Get live price directly from broker connector.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTCUSDT")

        Returns:
            Current price or None if not available
        """
        try:
            # Determine broker based on symbol format
            if "/" in symbol or symbol.endswith("USDT") or symbol.endswith("BTC"):
                # Crypto symbol
                connector = self.connectors.get("binance")
                broker_name = "binance"
            else:
                # Stock symbol
                connector = self.connectors.get("alpaca")
                broker_name = "alpaca"

            if not connector or not connector.is_connected():
                logger.warning(f"Connector {broker_name} not available for {symbol}")
                return None

            # Get latest quote from broker
            quote = await connector.get_latest_quote(symbol)

            if quote:
                # Calculate mid price from bid/ask
                if hasattr(quote, 'bid_price') and hasattr(quote, 'ask_price'):
                    price = (quote.bid_price + quote.ask_price) / 2
                elif hasattr(quote, 'price'):
                    price = quote.price
                else:
                    logger.warning(f"Quote for {symbol} has no price data")
                    return None

                logger.info(f"Live price for {symbol}: ${price:.2f}")
                return float(price)
            else:
                logger.warning(f"No quote received from {broker_name} for {symbol}")
                return None

        except Exception as e:
            logger.error(f"Error getting live price for {symbol}: {e}")
            return None

    def get_status(self) -> dict:
        """Get service status."""
        return {
            "connectors": {
                name: connector.is_connected()
                for name, connector in self.connectors.items()
            },
            "subscriptions": {
                broker: list(symbols)
                for broker, symbols in self.subscribed_symbols.items()
            },
            "websocket_clients": len(self.websocket_clients),
        }
