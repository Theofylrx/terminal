"""Base broker connector interface and utilities."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class MarketDataType(str, Enum):
    """Types of market data."""

    TRADE = "trade"
    QUOTE = "quote"
    BAR = "bar"
    ORDERBOOK = "orderbook"


class Trade(BaseModel):
    """Trade data model."""

    symbol: str
    price: float
    size: float
    timestamp: datetime
    exchange: Optional[str] = None
    conditions: Optional[List[str]] = None


class Quote(BaseModel):
    """Quote (bid/ask) data model."""

    symbol: str
    bid_price: float
    bid_size: float
    ask_price: float
    ask_size: float
    timestamp: datetime
    exchange: Optional[str] = None


class Bar(BaseModel):
    """OHLCV bar data model."""

    symbol: str
    timeframe: str  # 1m, 5m, 15m, 1h, 1D, etc.
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: datetime
    trade_count: Optional[int] = None
    vwap: Optional[float] = None


class OrderBook(BaseModel):
    """Order book snapshot."""

    symbol: str
    bids: List[List[float]]  # [[price, size], ...]
    asks: List[List[float]]
    timestamp: datetime


class BrokerConnector(ABC):
    """
    Abstract base class for broker connectors.

    All broker connectors must implement this interface to provide
    standardized access to market data from different sources.
    """

    def __init__(self, name: str):
        """Initialize connector."""
        self.name = name
        self.connected = False
        self.subscribed_symbols: Set[str] = set()
        self._callbacks: Dict[MarketDataType, List[Callable]] = {
            MarketDataType.TRADE: [],
            MarketDataType.QUOTE: [],
            MarketDataType.BAR: [],
            MarketDataType.ORDERBOOK: [],
        }
        self._reconnect_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 10
        self._base_reconnect_delay = 1.0
        self._max_reconnect_delay = 60.0
        self.logger = logging.getLogger(f"{__name__}.{name}")

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to the broker's data feed.

        Raises:
            ConnectionError: If connection fails.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the broker's data feed."""
        pass

    @abstractmethod
    async def subscribe(self, symbols: List[str], data_types: Optional[List[MarketDataType]] = None) -> None:
        """
        Subscribe to market data for given symbols.

        Args:
            symbols: List of symbols to subscribe to.
            data_types: Types of data to subscribe to (trades, quotes, bars).
                       If None, subscribe to all available types.
        """
        pass

    @abstractmethod
    async def unsubscribe(self, symbols: List[str]) -> None:
        """
        Unsubscribe from market data for given symbols.

        Args:
            symbols: List of symbols to unsubscribe from.
        """
        pass

    @abstractmethod
    async def get_historical_bars(
        self,
        symbol: str,
        timeframe: str,
        start: datetime,
        end: datetime,
        limit: Optional[int] = None,
    ) -> List[Bar]:
        """
        Fetch historical OHLCV bars.

        Args:
            symbol: Symbol to fetch data for.
            timeframe: Bar timeframe (1m, 5m, 1h, 1D, etc.).
            start: Start datetime.
            end: End datetime.
            limit: Maximum number of bars to return.

        Returns:
            List of OHLCV bars.
        """
        pass

    def register_callback(self, data_type: MarketDataType, callback: Callable) -> None:
        """
        Register a callback for a specific data type.

        Args:
            data_type: Type of market data.
            callback: Async function to call when data is received.
        """
        if callback not in self._callbacks[data_type]:
            self._callbacks[data_type].append(callback)
            self.logger.debug(f"Registered callback for {data_type.value}")

    def unregister_callback(self, data_type: MarketDataType, callback: Callable) -> None:
        """Unregister a callback."""
        if callback in self._callbacks[data_type]:
            self._callbacks[data_type].remove(callback)
            self.logger.debug(f"Unregistered callback for {data_type.value}")

    async def _emit(self, data_type: MarketDataType, data: Any) -> None:
        """Emit data to all registered callbacks."""
        callbacks = self._callbacks.get(data_type, [])
        if callbacks:
            await asyncio.gather(
                *[callback(data) for callback in callbacks],
                return_exceptions=True
            )

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection with exponential backoff."""
        self.connected = False
        self.logger.warning(f"{self.name} disconnected, attempting to reconnect...")

        while self._reconnect_attempts < self._max_reconnect_attempts:
            delay = min(
                self._base_reconnect_delay * (2 ** self._reconnect_attempts),
                self._max_reconnect_delay
            )
            self.logger.info(f"Reconnecting in {delay}s (attempt {self._reconnect_attempts + 1}/{self._max_reconnect_attempts})")

            await asyncio.sleep(delay)

            try:
                await self.connect()

                # Resubscribe to symbols
                if self.subscribed_symbols:
                    symbols = list(self.subscribed_symbols)
                    await self.subscribe(symbols)

                self.logger.info(f"{self.name} reconnected successfully")
                self._reconnect_attempts = 0
                return

            except Exception as e:
                self.logger.error(f"Reconnection attempt failed: {e}")
                self._reconnect_attempts += 1

        self.logger.error(f"{self.name} failed to reconnect after {self._max_reconnect_attempts} attempts")

    def is_connected(self) -> bool:
        """Check if connector is connected."""
        return self.connected

    def get_subscribed_symbols(self) -> Set[str]:
        """Get set of currently subscribed symbols."""
        return self.subscribed_symbols.copy()
