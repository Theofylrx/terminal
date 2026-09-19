"""Broker Factory - Abstraction layer for different broker integrations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class BrokerOrder:
    """Standardized broker order response."""

    def __init__(
        self,
        broker_order_id: str,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        status: OrderStatus,
        quantity: float,
        filled_quantity: float = 0.0,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        filled_price: Optional[float] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.broker_order_id = broker_order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.status = status
        self.quantity = quantity
        self.filled_quantity = filled_quantity
        self.limit_price = limit_price
        self.stop_price = stop_price
        self.filled_price = filled_price
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.raw_response = raw_response or {}


class BrokerPosition:
    """Standardized broker position response."""

    def __init__(
        self,
        symbol: str,
        quantity: float,
        avg_entry_price: float,
        current_price: float,
        market_value: float,
        unrealized_pnl: float,
        side: str,  # "long" or "short"
        raw_response: Optional[Dict[str, Any]] = None,
    ):
        self.symbol = symbol
        self.quantity = quantity
        self.avg_entry_price = avg_entry_price
        self.current_price = current_price
        self.market_value = market_value
        self.unrealized_pnl = unrealized_pnl
        self.side = side
        self.raw_response = raw_response or {}


class BrokerClient(ABC):
    """
    Abstract base class for broker integrations.

    Each broker (Alpaca, Binance, Interactive Brokers, etc.) implements this interface.
    This provides a consistent API regardless of which broker the user chooses.
    """

    def __init__(self, api_key: str, api_secret: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize broker client.

        Args:
            api_key: Decrypted API key
            api_secret: Decrypted API secret
            config: Broker-specific configuration
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.config = config or {}

    @abstractmethod
    async def verify_connection(self) -> bool:
        """
        Verify broker connection and credentials.

        Returns:
            True if connection successful, False otherwise

        Raises:
            Exception with error details if connection fails
        """
        pass

    @abstractmethod
    async def get_account(self) -> Dict[str, Any]:
        """
        Get account information (balance, buying power, etc.).

        Returns:
            Dictionary with account details
        """
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> BrokerOrder:
        """
        Place an order.

        Args:
            symbol: Trading symbol (e.g., "BTCUSD", "AAPL")
            side: Buy or sell
            order_type: Market, limit, stop, etc.
            quantity: Order quantity
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            BrokerOrder object with order details

        Raises:
            Exception if order placement fails
        """
        pass

    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            broker_order_id: Broker's order ID

        Returns:
            True if cancellation successful

        Raises:
            Exception if cancellation fails
        """
        pass

    @abstractmethod
    async def get_order(self, broker_order_id: str) -> BrokerOrder:
        """
        Get order status.

        Args:
            broker_order_id: Broker's order ID

        Returns:
            BrokerOrder object

        Raises:
            Exception if order not found
        """
        pass

    @abstractmethod
    async def get_positions(self) -> List[BrokerPosition]:
        """
        Get all open positions.

        Returns:
            List of BrokerPosition objects
        """
        pass

    @abstractmethod
    async def close_position(self, symbol: str) -> BrokerOrder:
        """
        Close a position.

        Args:
            symbol: Symbol to close

        Returns:
            BrokerOrder for the closing order

        Raises:
            Exception if position close fails
        """
        pass


class AlpacaBrokerClient(BrokerClient):
    """Alpaca broker implementation."""

    async def verify_connection(self) -> bool:
        # TODO: Implement Alpaca connection verification
        # from alpaca.trading.client import TradingClient
        # client = TradingClient(self.api_key, self.api_secret)
        # account = client.get_account()
        # return account is not None
        raise NotImplementedError("Alpaca integration pending")

    async def get_account(self) -> Dict[str, Any]:
        raise NotImplementedError("Alpaca integration pending")

    async def place_order(self, symbol, side, order_type, quantity, limit_price=None, stop_price=None) -> BrokerOrder:
        raise NotImplementedError("Alpaca integration pending")

    async def cancel_order(self, broker_order_id: str) -> bool:
        raise NotImplementedError("Alpaca integration pending")

    async def get_order(self, broker_order_id: str) -> BrokerOrder:
        raise NotImplementedError("Alpaca integration pending")

    async def get_positions(self) -> List[BrokerPosition]:
        raise NotImplementedError("Alpaca integration pending")

    async def close_position(self, symbol: str) -> BrokerOrder:
        raise NotImplementedError("Alpaca integration pending")


class BinanceBrokerClient(BrokerClient):
    """Binance broker implementation."""

    async def verify_connection(self) -> bool:
        # TODO: Implement Binance connection verification
        raise NotImplementedError("Binance integration pending")

    async def get_account(self) -> Dict[str, Any]:
        raise NotImplementedError("Binance integration pending")

    async def place_order(self, symbol, side, order_type, quantity, limit_price=None, stop_price=None) -> BrokerOrder:
        raise NotImplementedError("Binance integration pending")

    async def cancel_order(self, broker_order_id: str) -> bool:
        raise NotImplementedError("Binance integration pending")

    async def get_order(self, broker_order_id: str) -> BrokerOrder:
        raise NotImplementedError("Binance integration pending")

    async def get_positions(self) -> List[BrokerPosition]:
        raise NotImplementedError("Binance integration pending")

    async def close_position(self, symbol: str) -> BrokerOrder:
        raise NotImplementedError("Binance integration pending")


class InteractiveBrokersBrokerClient(BrokerClient):
    """Interactive Brokers implementation."""

    async def verify_connection(self) -> bool:
        # TODO: Implement IB connection verification
        raise NotImplementedError("Interactive Brokers integration pending")

    async def get_account(self) -> Dict[str, Any]:
        raise NotImplementedError("Interactive Brokers integration pending")

    async def place_order(self, symbol, side, order_type, quantity, limit_price=None, stop_price=None) -> BrokerOrder:
        raise NotImplementedError("Interactive Brokers integration pending")

    async def cancel_order(self, broker_order_id: str) -> bool:
        raise NotImplementedError("Interactive Brokers integration pending")

    async def get_order(self, broker_order_id: str) -> BrokerOrder:
        raise NotImplementedError("Interactive Brokers integration pending")

    async def get_positions(self) -> List[BrokerPosition]:
        raise NotImplementedError("Interactive Brokers integration pending")

    async def close_position(self, symbol: str) -> BrokerOrder:
        raise NotImplementedError("Interactive Brokers integration pending")


class BrokerFactory:
    """
    Factory for creating broker clients.

    This ensures we return the correct broker implementation based on user's choice.
    """

    _clients = {
        "alpaca": AlpacaBrokerClient,
        "binance": BinanceBrokerClient,
        "interactive_brokers": InteractiveBrokersBrokerClient,
    }

    @classmethod
    def create_client(
        cls,
        broker_name: str,
        api_key: str,
        api_secret: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> BrokerClient:
        """
        Create a broker client.

        Args:
            broker_name: Name of the broker (e.g., "alpaca", "binance")
            api_key: Decrypted API key
            api_secret: Decrypted API secret
            config: Broker-specific configuration

        Returns:
            BrokerClient instance

        Raises:
            ValueError: If broker not supported
        """
        client_class = cls._clients.get(broker_name.lower())

        if not client_class:
            supported = ", ".join(cls._clients.keys())
            raise ValueError(f"Unsupported broker: {broker_name}. Supported brokers: {supported}")

        return client_class(api_key, api_secret, config)

    @classmethod
    def register_broker(cls, broker_name: str, client_class: type):
        """
        Register a new broker implementation.

        This allows adding new brokers without modifying the factory.

        Args:
            broker_name: Name of the broker
            client_class: BrokerClient subclass
        """
        cls._clients[broker_name.lower()] = client_class

    @classmethod
    def get_supported_brokers(cls) -> List[str]:
        """Get list of supported broker names."""
        return list(cls._clients.keys())
