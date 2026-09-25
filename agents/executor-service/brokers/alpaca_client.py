"""
Alpaca Broker Client
Integration with Alpaca Trading API for order execution
"""

from typing import Optional, List
from datetime import datetime
import httpx

from .base import (
    BrokerClient,
    BrokerOrder,
    BrokerPosition,
    OrderSide,
    OrderType,
    OrderStatus
)


class AlpacaBrokerClient(BrokerClient):
    """
    Alpaca broker client for executing stock trades.

    Uses Alpaca Trading API v2 for order execution.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://paper-api.alpaca.markets"
    ):
        """
        Initialize Alpaca broker client.

        Args:
            api_key: Alpaca API key
            api_secret: Alpaca API secret
            base_url: Base URL (paper or live trading)
        """
        super().__init__("alpaca")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        # HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": api_secret,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def connect(self) -> None:
        """Verify connection to Alpaca API."""
        try:
            self.logger.info("Connecting to Alpaca Trading API")

            # Test connection by fetching account
            response = await self.client.get(f"{self.base_url}/v2/account")
            response.raise_for_status()

            account = response.json()
            self.connected = True

            self.logger.info(
                f"Connected to Alpaca (Account: {account.get('account_number')}, "
                f"Balance: ${account.get('cash', 0)})"
            )

        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Alpaca: {e}")
            raise ConnectionError(f"Alpaca connection failed: {e}")

    async def disconnect(self) -> None:
        """Close HTTP client."""
        self.logger.info("Disconnecting from Alpaca")
        await self.client.aclose()
        self.connected = False

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
        Submit an order to Alpaca.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            side: BUY or SELL
            quantity: Number of shares
            order_type: Order type
            limit_price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            time_in_force: gtc, day, ioc, fok

        Returns:
            BrokerOrder with order details
        """
        try:
            # Map our enums to Alpaca format
            alpaca_side = side.value.lower()
            alpaca_type = self._map_order_type(order_type)

            # Build order payload
            payload = {
                "symbol": symbol.upper(),
                "qty": int(quantity),  # Alpaca uses integer quantities for stocks
                "side": alpaca_side,
                "type": alpaca_type,
                "time_in_force": time_in_force
            }

            # Add prices based on order type
            if order_type == OrderType.LIMIT and limit_price:
                payload["limit_price"] = str(limit_price)
            elif order_type == OrderType.STOP_LOSS and stop_price:
                payload["stop_price"] = str(stop_price)
            elif order_type == OrderType.STOP_LIMIT and stop_price and limit_price:
                payload["stop_price"] = str(stop_price)
                payload["limit_price"] = str(limit_price)

            self.logger.info(f"Submitting Alpaca order: {payload}")

            # Submit order
            response = await self.client.post(
                f"{self.base_url}/v2/orders",
                json=payload
            )
            response.raise_for_status()

            order_data = response.json()
            broker_order = self._parse_order(order_data)

            self.logger.info(
                f"Order submitted successfully: {broker_order.broker_order_id} "
                f"({symbol}, {side.value}, {quantity} shares)"
            )

            return broker_order

        except httpx.HTTPStatusError as e:
            error_msg = f"Alpaca order submission failed: {e.response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to submit Alpaca order: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an Alpaca order."""
        try:
            self.logger.info(f"Cancelling Alpaca order: {broker_order_id}")

            response = await self.client.delete(
                f"{self.base_url}/v2/orders/{broker_order_id}"
            )
            response.raise_for_status()

            self.logger.info(f"Order cancelled: {broker_order_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel order {broker_order_id}: {e}")
            raise Exception(f"Order cancellation failed: {e}")

    async def get_order_status(self, broker_order_id: str) -> BrokerOrder:
        """Get Alpaca order status."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v2/orders/{broker_order_id}"
            )
            response.raise_for_status()

            order_data = response.json()
            return self._parse_order(order_data)

        except Exception as e:
            error_msg = f"Failed to get order status: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_account_balance(self) -> float:
        """Get Alpaca account balance."""
        try:
            response = await self.client.get(f"{self.base_url}/v2/account")
            response.raise_for_status()

            account = response.json()
            cash = float(account.get("cash", 0))

            self.logger.debug(f"Account balance: ${cash:.2f}")
            return cash

        except Exception as e:
            error_msg = f"Failed to get account balance: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_position(self, symbol: str) -> Optional[BrokerPosition]:
        """Get Alpaca position for a symbol."""
        try:
            response = await self.client.get(
                f"{self.base_url}/v2/positions/{symbol.upper()}"
            )

            if response.status_code == 404:
                return None  # No position

            response.raise_for_status()
            position_data = response.json()

            return self._parse_position(position_data)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"Failed to get position: {e}")
        except Exception as e:
            raise Exception(f"Failed to get position: {e}")

    async def get_all_positions(self) -> List[BrokerPosition]:
        """Get all Alpaca positions."""
        try:
            response = await self.client.get(f"{self.base_url}/v2/positions")
            response.raise_for_status()

            positions_data = response.json()
            positions = [self._parse_position(p) for p in positions_data]

            self.logger.debug(f"Retrieved {len(positions)} positions")
            return positions

        except Exception as e:
            error_msg = f"Failed to get positions: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def close_position(self, symbol: str) -> BrokerOrder:
        """Close an Alpaca position."""
        try:
            self.logger.info(f"Closing position: {symbol}")

            # Alpaca has a dedicated close position endpoint
            response = await self.client.delete(
                f"{self.base_url}/v2/positions/{symbol.upper()}"
            )
            response.raise_for_status()

            order_data = response.json()
            broker_order = self._parse_order(order_data)

            self.logger.info(f"Position closed: {symbol}")
            return broker_order

        except Exception as e:
            error_msg = f"Failed to close position {symbol}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    # ==================== Helper Methods ====================

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map our OrderType to Alpaca format."""
        mapping = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP_LOSS: "stop",
            OrderType.STOP_LIMIT: "stop_limit",
            OrderType.TRAILING_STOP: "trailing_stop"
        }
        return mapping.get(order_type, "market")

    def _map_order_status(self, alpaca_status: str) -> OrderStatus:
        """Map Alpaca status to our OrderStatus."""
        mapping = {
            "new": OrderStatus.SUBMITTED,
            "pending_new": OrderStatus.PENDING,
            "accepted": OrderStatus.ACCEPTED,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.EXPIRED,
            "replaced": OrderStatus.CANCELLED,
            "pending_cancel": OrderStatus.PENDING,
            "pending_replace": OrderStatus.PENDING,
            "rejected": OrderStatus.REJECTED,
            "stopped": OrderStatus.CANCELLED,
            "suspended": OrderStatus.PENDING
        }
        return mapping.get(alpaca_status, OrderStatus.PENDING)

    def _parse_order(self, order_data: dict) -> BrokerOrder:
        """Parse Alpaca order response to BrokerOrder."""
        # Map Alpaca side to our OrderSide enum
        alpaca_side = order_data["side"].lower()
        side = OrderSide.BUY if alpaca_side == "buy" else OrderSide.SELL

        return BrokerOrder(
            broker_order_id=order_data["id"],
            symbol=order_data["symbol"],
            side=side,
            order_type=self._reverse_map_order_type(order_data["type"]),
            status=self._map_order_status(order_data["status"]),
            quantity=float(order_data["qty"]),
            filled_quantity=float(order_data.get("filled_qty", 0)),
            limit_price=float(order_data["limit_price"]) if order_data.get("limit_price") else None,
            stop_price=float(order_data["stop_price"]) if order_data.get("stop_price") else None,
            avg_fill_price=float(order_data["filled_avg_price"]) if order_data.get("filled_avg_price") else None,
            created_at=datetime.fromisoformat(order_data["created_at"].replace("Z", "+00:00")),
            filled_at=datetime.fromisoformat(order_data["filled_at"].replace("Z", "+00:00")) if order_data.get("filled_at") else None
        )

    def _reverse_map_order_type(self, alpaca_type: str) -> OrderType:
        """Reverse map Alpaca type to our OrderType."""
        mapping = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP_LOSS,
            "stop_limit": OrderType.STOP_LIMIT,
            "trailing_stop": OrderType.TRAILING_STOP
        }
        return mapping.get(alpaca_type, OrderType.MARKET)

    def _parse_position(self, position_data: dict) -> BrokerPosition:
        """Parse Alpaca position response to BrokerPosition."""
        qty = float(position_data["qty"])
        side = "long" if qty > 0 else "short"

        return BrokerPosition(
            symbol=position_data["symbol"],
            quantity=abs(qty),
            avg_entry_price=float(position_data["avg_entry_price"]),
            current_price=float(position_data["current_price"]),
            market_value=float(position_data["market_value"]),
            cost_basis=float(position_data["cost_basis"]),
            unrealized_pnl=float(position_data["unrealized_pl"]),
            side=side
        )
