"""
Base Broker Client
Abstract base class for broker integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum
import logging


class OrderStatus(str, Enum):
    """Order status enum."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class OrderSide(str, Enum):
    """Order side enum."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enum."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


@dataclass
class BrokerOrder:
    """Broker order data structure."""
    broker_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    quantity: float
    filled_quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    avg_fill_price: Optional[float] = None
    commission: Optional[float] = None
    created_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    error_message: Optional[str] = None


@dataclass
class BrokerPosition:
    """Broker position data structure."""
    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    market_value: float
    cost_basis: float
    unrealized_pnl: float
    side: str  # "long" or "short"


class BrokerClient(ABC):
    """
    Abstract base class for broker clients.

    All broker integrations must implement these methods.
    """

    def __init__(self, broker_name: str):
        """Initialize broker client."""
        self.broker_name = broker_name
        self.logger = logging.getLogger(f"{__name__}.{broker_name}")
        self.connected = False

    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to broker API.

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to broker API."""
        pass

    @abstractmethod
    async def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "gtc"
    ) -> BrokerOrder:
        """
        Submit an order to the broker.

        Args:
            symbol: Trading symbol
            side: BUY or SELL
            quantity: Number of units
            order_type: Order type (MARKET, LIMIT, etc.)
            limit_price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            time_in_force: Time in force (gtc, ioc, fok, day)

        Returns:
            BrokerOrder with order details

        Raises:
            Exception: If order submission fails
        """
        pass

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            broker_order_id: Broker's order ID

        Returns:
            True if cancelled successfully

        Raises:
            Exception: If cancellation fails
        """
        pass

    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> BrokerOrder:
        """
        Get current status of an order.

        Args:
            broker_order_id: Broker's order ID

        Returns:
            BrokerOrder with current status

        Raises:
            Exception: If order not found
        """
        pass

    @abstractmethod
    async def get_account_balance(self) -> float:
        """
        Get current account balance.

        Returns:
            Account balance in USD

        Raises:
            Exception: If balance retrieval fails
        """
        pass

    @abstractmethod
    async def get_position(self, symbol: str) -> Optional[BrokerPosition]:
        """
        Get current position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            BrokerPosition if position exists, None otherwise

        Raises:
            Exception: If position retrieval fails
        """
        pass

    @abstractmethod
    async def get_all_positions(self) -> List[BrokerPosition]:
        """
        Get all open positions.

        Returns:
            List of BrokerPosition objects

        Raises:
            Exception: If positions retrieval fails
        """
        pass

    @abstractmethod
    async def close_position(self, symbol: str) -> BrokerOrder:
        """
        Close an entire position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            BrokerOrder for the closing order

        Raises:
            Exception: If position close fails
        """
        pass

    def is_connected(self) -> bool:
        """Check if connected to broker."""
        return self.connected
