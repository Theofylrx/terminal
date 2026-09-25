"""
Order Executor
Orchestrates order execution: risk checks, position sizing, broker submission
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from brokers import BrokerClient, OrderSide as BrokerOrderSide, OrderType as BrokerOrderType
from position_sizer import PositionSizer
from risk_manager import RiskManager
from models.schemas import (
    ExecuteOrderRequest,
    ExecuteOrderResponse,
    OrderSide,
    OrderType,
    AssetClass
)


class OrderExecutor:
    """
    Order execution orchestrator.

    Coordinates:
    1. Risk validation
    2. Position sizing
    3. Broker submission
    4. Order monitoring
    5. Database updates
    """

    def __init__(
        self,
        alpaca_client: Optional[BrokerClient] = None,
        binance_client: Optional[BrokerClient] = None,
        position_sizer: Optional[PositionSizer] = None,
        risk_manager: Optional[RiskManager] = None
    ):
        """
        Initialize order executor.

        Args:
            alpaca_client: Alpaca broker client
            binance_client: Binance broker client
            position_sizer: Position sizing service
            risk_manager: Risk management service
        """
        self.logger = logging.getLogger(__name__)

        # Broker clients
        self.alpaca_client = alpaca_client
        self.binance_client = binance_client

        # Services
        self.position_sizer = position_sizer or PositionSizer()
        self.risk_manager = risk_manager or RiskManager()

    async def execute_order(
        self,
        order_request: ExecuteOrderRequest,
        account_balance: float,
        open_positions: list,
        daily_trades_count: int = 0,
        daily_pnl: float = 0.0,
        perform_risk_check: bool = True
    ) -> ExecuteOrderResponse:
        """
        Execute a trade order.

        Process:
        1. Select broker based on asset class
        2. Perform risk check (if enabled)
        3. Submit order to broker
        4. Return execution result

        Args:
            order_request: Order execution request
            account_balance: Current account balance
            open_positions: List of open positions
            daily_trades_count: Number of trades today
            daily_pnl: P&L for today
            perform_risk_check: Whether to run risk check

        Returns:
            ExecuteOrderResponse with execution details
        """
        try:
            self.logger.info(
                f"Executing order: {order_request.symbol} {order_request.side.value} "
                f"{order_request.quantity} @ {order_request.order_type.value}"
            )

            # 1. Select broker
            broker_client = self._select_broker(order_request.asset_class)
            if not broker_client:
                return ExecuteOrderResponse(
                    success=False,
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    status="REJECTED",
                    error_message=f"No broker available for {order_request.asset_class.value}"
                )

            # 2. Risk check (if enabled)
            if perform_risk_check:
                risk_result = await self.risk_manager.check_risk(
                    user_id=order_request.user_id,
                    symbol=order_request.symbol,
                    side=order_request.side.value,
                    quantity=order_request.quantity,
                    entry_price=self._get_entry_price(order_request),
                    stop_loss_price=order_request.stop_loss_price,
                    account_balance=account_balance,
                    open_positions=open_positions,
                    daily_trades_count=daily_trades_count,
                    daily_pnl=daily_pnl
                )

                if not risk_result.approved:
                    self.logger.warning(
                        f"Order rejected by risk manager: {risk_result.violations}"
                    )
                    return ExecuteOrderResponse(
                        success=False,
                        symbol=order_request.symbol,
                        side=order_request.side,
                        quantity=order_request.quantity,
                        status="REJECTED",
                        error_message=f"Risk check failed: {', '.join(risk_result.violations)}"
                    )

                if risk_result.warnings:
                    self.logger.warning(f"Risk warnings: {risk_result.warnings}")

            # 3. Submit order to broker
            try:
                broker_order = await broker_client.submit_order(
                    symbol=order_request.symbol,
                    side=self._map_order_side(order_request.side),
                    quantity=order_request.quantity,
                    order_type=self._map_order_type(order_request.order_type),
                    limit_price=order_request.limit_price,
                    stop_price=order_request.stop_price,
                    time_in_force="gtc"
                )

                # 4. Build successful response
                response = ExecuteOrderResponse(
                    success=True,
                    order_id=None,  # Will be set by repository layer
                    broker_order_id=broker_order.broker_order_id,
                    symbol=broker_order.symbol,
                    side=order_request.side,
                    quantity=broker_order.quantity,
                    status=broker_order.status.value.upper(),
                    filled_quantity=broker_order.filled_quantity,
                    avg_fill_price=broker_order.avg_fill_price,
                    commission=broker_order.commission,
                    submitted_at=broker_order.created_at or datetime.utcnow(),
                    filled_at=broker_order.filled_at
                )

                self.logger.info(
                    f"Order executed successfully: {broker_order.broker_order_id} "
                    f"({broker_order.status.value})"
                )

                return response

            except Exception as e:
                error_msg = f"Broker order submission failed: {str(e)}"
                self.logger.error(error_msg)

                return ExecuteOrderResponse(
                    success=False,
                    symbol=order_request.symbol,
                    side=order_request.side,
                    quantity=order_request.quantity,
                    status="REJECTED",
                    error_message=error_msg
                )

        except Exception as e:
            error_msg = f"Order execution failed: {str(e)}"
            self.logger.error(error_msg)

            return ExecuteOrderResponse(
                success=False,
                symbol=order_request.symbol,
                side=order_request.side,
                quantity=order_request.quantity,
                status="REJECTED",
                error_message=error_msg
            )

    async def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_per_trade_percent: float = 1.0,
        risk_multiplier: float = 1.0
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size.

        Args:
            account_balance: Account balance
            entry_price: Entry price
            stop_loss_price: Stop loss price
            risk_per_trade_percent: Risk percentage
            risk_multiplier: Risk multiplier from strategy

        Returns:
            Position sizing details
        """
        try:
            quantity, details = self.position_sizer.calculate_position_size(
                account_balance=account_balance,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price,
                risk_per_trade_percent=risk_per_trade_percent,
                risk_multiplier=risk_multiplier
            )

            return {
                "success": True,
                "quantity": quantity,
                **details
            }

        except Exception as e:
            self.logger.error(f"Position size calculation failed: {e}")
            return {
                "success": False,
                "error_message": str(e)
            }

    async def check_order_status(
        self,
        broker_order_id: str,
        symbol: str,
        asset_class: AssetClass
    ) -> Optional[Dict[str, Any]]:
        """
        Check status of an order.

        Args:
            broker_order_id: Broker's order ID
            symbol: Trading symbol
            asset_class: Asset type

        Returns:
            Order status details or None if not found
        """
        try:
            broker_client = self._select_broker(asset_class)
            if not broker_client:
                self.logger.error(f"No broker for {asset_class.value}")
                return None

            # Binance requires symbol for order status
            if broker_client == self.binance_client:
                broker_order = await broker_client.get_order_status(
                    broker_order_id=broker_order_id,
                    symbol=symbol
                )
            else:
                broker_order = await broker_client.get_order_status(
                    broker_order_id=broker_order_id
                )

            return {
                "broker_order_id": broker_order.broker_order_id,
                "symbol": broker_order.symbol,
                "status": broker_order.status.value.upper(),
                "quantity": broker_order.quantity,
                "filled_quantity": broker_order.filled_quantity,
                "avg_fill_price": broker_order.avg_fill_price,
                "created_at": broker_order.created_at,
                "filled_at": broker_order.filled_at
            }

        except Exception as e:
            self.logger.error(f"Failed to get order status: {e}")
            return None

    async def cancel_order(
        self,
        broker_order_id: str,
        symbol: str,
        asset_class: AssetClass
    ) -> bool:
        """
        Cancel an order.

        Args:
            broker_order_id: Broker's order ID
            symbol: Trading symbol
            asset_class: Asset type

        Returns:
            True if cancelled successfully
        """
        try:
            broker_client = self._select_broker(asset_class)
            if not broker_client:
                self.logger.error(f"No broker for {asset_class.value}")
                return False

            # Binance requires symbol for cancellation
            if broker_client == self.binance_client:
                success = await broker_client.cancel_order(
                    broker_order_id=broker_order_id,
                    symbol=symbol
                )
            else:
                success = await broker_client.cancel_order(
                    broker_order_id=broker_order_id
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            return False

    # ==================== Helper Methods ====================

    def _select_broker(self, asset_class: AssetClass) -> Optional[BrokerClient]:
        """Select appropriate broker based on asset class."""
        if asset_class == AssetClass.STOCK:
            return self.alpaca_client
        elif asset_class == AssetClass.CRYPTO:
            return self.binance_client
        elif asset_class == AssetClass.FOREX:
            # TODO: Add OANDA client for forex
            return None
        else:
            return None

    def _map_order_side(self, side: OrderSide) -> BrokerOrderSide:
        """Map API order side to broker order side."""
        if side == OrderSide.BUY:
            return BrokerOrderSide.BUY
        else:
            return BrokerOrderSide.SELL

    def _map_order_type(self, order_type: OrderType) -> BrokerOrderType:
        """Map API order type to broker order type."""
        mapping = {
            OrderType.MARKET: BrokerOrderType.MARKET,
            OrderType.LIMIT: BrokerOrderType.LIMIT,
            OrderType.STOP_LOSS: BrokerOrderType.STOP_LOSS,
            OrderType.STOP_LIMIT: BrokerOrderType.STOP_LIMIT,
            OrderType.TRAILING_STOP: BrokerOrderType.TRAILING_STOP
        }
        return mapping.get(order_type, BrokerOrderType.MARKET)

    def _get_entry_price(self, order_request: ExecuteOrderRequest) -> float:
        """Get expected entry price from order request."""
        if order_request.order_type == OrderType.LIMIT and order_request.limit_price:
            return order_request.limit_price
        elif order_request.stop_price:
            return order_request.stop_price
        else:
            # For market orders, we don't know exact price yet
            # Caller should provide current market price if needed
            return 0.0
