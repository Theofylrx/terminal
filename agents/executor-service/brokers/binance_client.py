"""
Binance Broker Client
Integration with Binance API for crypto order execution
"""

from typing import Optional, List
from datetime import datetime
import time
import hmac
import hashlib
from urllib.parse import urlencode
import httpx

from .base import (
    BrokerClient,
    BrokerOrder,
    BrokerPosition,
    OrderSide,
    OrderType,
    OrderStatus
)


class BinanceBrokerClient(BrokerClient):
    """
    Binance broker client for executing crypto trades.

    Uses Binance Spot API for order execution.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://testnet.binance.vision"
    ):
        """
        Initialize Binance broker client.

        Args:
            api_key: Binance API key
            api_secret: Binance API secret
            base_url: Base URL (testnet or live trading)
        """
        super().__init__("binance")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")

        # HTTP client
        self.client = httpx.AsyncClient(
            headers={
                "X-MBX-APIKEY": api_key,
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def connect(self) -> None:
        """Verify connection to Binance API."""
        try:
            self.logger.info("Connecting to Binance API")

            # Test connection by fetching account info
            params = {"timestamp": int(time.time() * 1000)}
            params["signature"] = self._generate_signature(params)

            response = await self.client.get(
                f"{self.base_url}/api/v3/account",
                params=params
            )
            response.raise_for_status()

            account = response.json()
            self.connected = True

            # Calculate total balance
            total_balance_usdt = sum(
                float(balance["free"]) + float(balance["locked"])
                for balance in account.get("balances", [])
                if balance["asset"] == "USDT"
            )

            self.logger.info(
                f"Connected to Binance (USDT Balance: ${total_balance_usdt:.2f})"
            )

        except Exception as e:
            self.connected = False
            self.logger.error(f"Failed to connect to Binance: {e}")
            raise ConnectionError(f"Binance connection failed: {e}")

    async def disconnect(self) -> None:
        """Close HTTP client."""
        self.logger.info("Disconnecting from Binance")
        await self.client.aclose()
        self.connected = False

    # Minimum notional values for common pairs (USDT)
    MIN_NOTIONAL = {
        "BTCUSDT": 10.0,
        "ETHUSDT": 10.0,
        "BNBUSDT": 10.0,
        "DEFAULT": 10.0  # Binance default minimum
    }

    async def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC"
    ) -> BrokerOrder:
        """
        Submit an order to Binance.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            side: BUY or SELL
            quantity: Quantity to trade
            order_type: Order type
            limit_price: Limit price (for LIMIT orders)
            stop_price: Stop price (for STOP orders)
            time_in_force: GTC, IOC, FOK

        Returns:
            BrokerOrder with order details
        """
        try:
            # Validate minimum notional value before submitting
            min_notional = self.MIN_NOTIONAL.get(symbol.upper(), self.MIN_NOTIONAL["DEFAULT"])

            # Calculate order value
            if order_type == OrderType.MARKET:
                # For market orders, fetch current price
                current_price = await self._get_current_price(symbol)
                if current_price == 0.0:
                    raise Exception(f"Failed to fetch current price for {symbol}")
                order_value = quantity * current_price
            elif order_type == OrderType.LIMIT and limit_price:
                order_value = quantity * limit_price
            else:
                # For other order types, use limit_price if available
                order_value = quantity * (limit_price or 0)

            # Validate against minimum notional
            if order_value < min_notional:
                raise Exception(
                    f"Order value ${order_value:.2f} is below Binance minimum ${min_notional:.2f} for {symbol}. "
                    f"Please increase quantity or choose a different symbol."
                )

            self.logger.info(
                f"Order validation passed: ${order_value:.2f} >= ${min_notional:.2f} minimum for {symbol}"
            )

            # Map our enums to Binance format
            binance_side = side.value.upper()
            binance_type = self._map_order_type(order_type)

            # Build order params
            params = {
                "symbol": symbol.upper(),
                "side": binance_side,
                "type": binance_type,
                "timestamp": int(time.time() * 1000)
            }

            # Add quantity (different format for market buy vs others)
            if order_type == OrderType.MARKET and side == OrderSide.BUY:
                # Market buy uses quoteOrderQty (USDT amount)
                # Use the validated order_value, rounded to 2 decimal places for USDT
                params["quoteOrderQty"] = f"{order_value:.2f}"
            else:
                params["quantity"] = str(quantity)

            # Add prices based on order type
            if order_type == OrderType.LIMIT:
                params["timeInForce"] = time_in_force
                params["price"] = str(limit_price)
            elif order_type == OrderType.STOP_LOSS:
                params["stopPrice"] = str(stop_price)
            elif order_type == OrderType.STOP_LIMIT:
                params["timeInForce"] = time_in_force
                params["price"] = str(limit_price)
                params["stopPrice"] = str(stop_price)

            # Add signature
            params["signature"] = self._generate_signature(params)

            self.logger.info(f"Submitting Binance order: {symbol} {binance_side} {quantity}")

            # Submit order
            response = await self.client.post(
                f"{self.base_url}/api/v3/order",
                params=params
            )
            response.raise_for_status()

            order_data = response.json()
            broker_order = self._parse_order(order_data)

            self.logger.info(
                f"Order submitted successfully: {broker_order.broker_order_id} "
                f"({symbol}, {side.value}, {quantity})"
            )

            return broker_order

        except httpx.HTTPStatusError as e:
            error_msg = f"Binance order submission failed: {e.response.text}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to submit Binance order: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def cancel_order(self, broker_order_id: str, symbol: str = None) -> bool:
        """
        Cancel a Binance order.

        Note: Binance requires symbol for cancellation.
        """
        try:
            if not symbol:
                raise ValueError("Symbol required to cancel Binance order")

            self.logger.info(f"Cancelling Binance order: {broker_order_id}")

            params = {
                "symbol": symbol.upper(),
                "orderId": broker_order_id,
                "timestamp": int(time.time() * 1000)
            }
            params["signature"] = self._generate_signature(params)

            response = await self.client.delete(
                f"{self.base_url}/api/v3/order",
                params=params
            )
            response.raise_for_status()

            self.logger.info(f"Order cancelled: {broker_order_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to cancel order {broker_order_id}: {e}")
            raise Exception(f"Order cancellation failed: {e}")

    async def get_order_status(self, broker_order_id: str, symbol: str = None) -> BrokerOrder:
        """
        Get Binance order status.

        Note: Binance requires symbol for order query.
        """
        try:
            if not symbol:
                raise ValueError("Symbol required to get Binance order status")

            params = {
                "symbol": symbol.upper(),
                "orderId": broker_order_id,
                "timestamp": int(time.time() * 1000)
            }
            params["signature"] = self._generate_signature(params)

            response = await self.client.get(
                f"{self.base_url}/api/v3/order",
                params=params
            )
            response.raise_for_status()

            order_data = response.json()
            return self._parse_order(order_data)

        except Exception as e:
            error_msg = f"Failed to get order status: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_account_balance(self) -> float:
        """Get Binance account balance (USDT)."""
        try:
            params = {"timestamp": int(time.time() * 1000)}
            params["signature"] = self._generate_signature(params)

            response = await self.client.get(
                f"{self.base_url}/api/v3/account",
                params=params
            )
            response.raise_for_status()

            account = response.json()

            # Get USDT balance
            usdt_balance = 0.0
            for balance in account.get("balances", []):
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"]) + float(balance["locked"])
                    break

            self.logger.debug(f"USDT balance: ${usdt_balance:.2f}")
            return usdt_balance

        except Exception as e:
            error_msg = f"Failed to get account balance: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def get_position(self, symbol: str) -> Optional[BrokerPosition]:
        """
        Get Binance position for a symbol.

        Note: Binance Spot doesn't have traditional positions.
        This returns the asset balance if any exists.
        """
        try:
            params = {"timestamp": int(time.time() * 1000)}
            params["signature"] = self._generate_signature(params)

            response = await self.client.get(
                f"{self.base_url}/api/v3/account",
                params=params
            )
            response.raise_for_status()

            account = response.json()

            # Extract base asset from symbol (e.g., "BTC" from "BTCUSDT")
            base_asset = symbol.replace("USDT", "").replace("BUSD", "")

            # Find balance for this asset
            for balance in account.get("balances", []):
                if balance["asset"] == base_asset:
                    free_qty = float(balance["free"])
                    locked_qty = float(balance["locked"])
                    total_qty = free_qty + locked_qty

                    if total_qty > 0:
                        # Get current price
                        current_price = await self._get_current_price(symbol)

                        return BrokerPosition(
                            symbol=symbol,
                            quantity=total_qty,
                            avg_entry_price=0.0,  # Not available in Spot
                            current_price=current_price,
                            market_value=total_qty * current_price,
                            cost_basis=0.0,  # Not available in Spot
                            unrealized_pnl=0.0,  # Not available in Spot
                            side="long"
                        )

            return None  # No position

        except Exception as e:
            raise Exception(f"Failed to get position: {e}")

    async def get_all_positions(self) -> List[BrokerPosition]:
        """Get all Binance positions (non-zero balances)."""
        try:
            params = {"timestamp": int(time.time() * 1000)}
            params["signature"] = self._generate_signature(params)

            response = await self.client.get(
                f"{self.base_url}/api/v3/account",
                params=params
            )
            response.raise_for_status()

            account = response.json()
            positions = []

            # Whitelist of major cryptocurrencies to check (avoids hundreds of testnet dust balances)
            MAJOR_CRYPTOS = [
                "BTC", "ETH", "BNB", "XRP", "ADA", "DOGE", "SOL", "TRX", "MATIC", "DOT",
                "LTC", "SHIB", "AVAX", "UNI", "ATOM", "LINK", "ETC", "XLM", "NEAR", "ALGO",
                "FIL", "VET", "SAND", "MANA", "AAVE", "AXS", "THETA", "FTM", "EGLD", "RUNE"
            ]

            # Get all non-zero balances for major cryptos only
            for balance in account.get("balances", []):
                asset = balance["asset"]

                # Skip stablecoins and non-major assets
                if asset in ["USDT", "BUSD", "USDC", "TUSD"] or asset not in MAJOR_CRYPTOS:
                    continue

                free_qty = float(balance["free"])
                locked_qty = float(balance["locked"])
                total_qty = free_qty + locked_qty

                if total_qty > 0:
                    symbol = f"{asset}USDT"

                    try:
                        current_price = await self._get_current_price(symbol)

                        # Skip if position value < $1 (filters out tiny balances)
                        position_value = total_qty * current_price
                        if position_value < 1.0:
                            continue

                        positions.append(BrokerPosition(
                            symbol=symbol,
                            quantity=total_qty,
                            avg_entry_price=0.0,
                            current_price=current_price,
                            market_value=total_qty * current_price,
                            cost_basis=0.0,
                            unrealized_pnl=0.0,
                            side="long"
                        ))
                    except:
                        # Skip if price not available
                        pass

            self.logger.debug(f"Retrieved {len(positions)} positions")
            return positions

        except Exception as e:
            error_msg = f"Failed to get positions: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    async def close_position(self, symbol: str) -> BrokerOrder:
        """Close a Binance position (sell all of asset)."""
        try:
            self.logger.info(f"Closing position: {symbol}")

            # Get current position
            position = await self.get_position(symbol)
            if not position:
                raise Exception(f"No position found for {symbol}")

            # Submit sell order for entire quantity
            return await self.submit_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=position.quantity,
                order_type=OrderType.MARKET
            )

        except Exception as e:
            error_msg = f"Failed to close position {symbol}: {e}"
            self.logger.error(error_msg)
            raise Exception(error_msg)

    # ==================== Helper Methods ====================

    def _generate_signature(self, params: dict) -> str:
        """Generate HMAC SHA256 signature for Binance API."""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map our OrderType to Binance format."""
        mapping = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP_LOSS: "STOP_LOSS",
            OrderType.STOP_LIMIT: "STOP_LOSS_LIMIT",
            OrderType.TRAILING_STOP: "TRAILING_STOP_MARKET"
        }
        return mapping.get(order_type, "MARKET")

    def _map_order_status(self, binance_status: str) -> OrderStatus:
        """Map Binance status to our OrderStatus."""
        mapping = {
            "NEW": OrderStatus.SUBMITTED,
            "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
            "FILLED": OrderStatus.FILLED,
            "CANCELED": OrderStatus.CANCELLED,
            "PENDING_CANCEL": OrderStatus.PENDING,
            "REJECTED": OrderStatus.REJECTED,
            "EXPIRED": OrderStatus.EXPIRED
        }
        return mapping.get(binance_status, OrderStatus.PENDING)

    def _parse_order(self, order_data: dict) -> BrokerOrder:
        """Parse Binance order response to BrokerOrder."""
        # Map Binance side to OrderSide enum (Binance returns uppercase "BUY"/"SELL")
        binance_side = order_data["side"].lower()
        side = OrderSide.BUY if binance_side == "buy" else OrderSide.SELL

        return BrokerOrder(
            broker_order_id=str(order_data["orderId"]),
            symbol=order_data["symbol"],
            side=side,
            order_type=self._reverse_map_order_type(order_data["type"]),
            status=self._map_order_status(order_data["status"]),
            quantity=float(order_data.get("origQty", 0)),
            filled_quantity=float(order_data.get("executedQty", 0)),
            limit_price=float(order_data["price"]) if order_data.get("price") and float(order_data["price"]) > 0 else None,
            stop_price=float(order_data["stopPrice"]) if order_data.get("stopPrice") and float(order_data["stopPrice"]) > 0 else None,
            avg_fill_price=float(order_data.get("avgPrice", 0)) if order_data.get("avgPrice") else None,
            created_at=datetime.fromtimestamp(order_data["time"] / 1000) if order_data.get("time") else None,
            filled_at=datetime.fromtimestamp(order_data["updateTime"] / 1000) if order_data.get("updateTime") and order_data["status"] == "FILLED" else None
        )

    def _reverse_map_order_type(self, binance_type: str) -> OrderType:
        """Reverse map Binance type to our OrderType."""
        mapping = {
            "MARKET": OrderType.MARKET,
            "LIMIT": OrderType.LIMIT,
            "STOP_LOSS": OrderType.STOP_LOSS,
            "STOP_LOSS_LIMIT": OrderType.STOP_LIMIT,
            "TRAILING_STOP_MARKET": OrderType.TRAILING_STOP
        }
        return mapping.get(binance_type, OrderType.MARKET)

    async def _get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol."""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v3/ticker/price",
                params={"symbol": symbol.upper()}
            )
            response.raise_for_status()

            data = response.json()
            return float(data["price"])

        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            return 0.0
