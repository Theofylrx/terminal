"""
Executor Service API Routes
FastAPI endpoints for order execution and position management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import logging

from models.schemas import (
    ExecuteOrderRequest,
    ExecuteOrderResponse,
    PositionSizeRequest,
    PositionSizeResponse,
    RiskCheckRequest,
    RiskCheckResponse,
    HealthResponse,
    PositionResponse,
    PositionsResponse,
    AccountResponse,
    ClosePositionResponse
)
from order_manager import OrderExecutor
from repositories import OrderRepository, PositionRepository
from brokers import AlpacaBrokerClient, BinanceBrokerClient
from position_sizer import PositionSizer
from risk_manager import RiskManager
from core.config import settings

# Import database session dependency (placeholder - update with actual path)
# from shared.database import get_session

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["executor"])


# Global instances (will be set by main.py)
_order_executor = None
_db_session = None


def get_order_executor() -> OrderExecutor:
    """Get order executor instance."""
    logger.debug(f"get_order_executor called, _order_executor is None: {_order_executor is None}")
    if _order_executor is None:
        raise RuntimeError("Order executor not initialized")
    return _order_executor


def set_order_executor(executor: OrderExecutor):
    """Set global order executor (called from main.py)."""
    global _order_executor
    _order_executor = executor
    logger.info(f"✅ Order executor set in routes module: {executor is not None}")


def get_db_session() -> AsyncSession:
    """Get database session."""
    # TODO: Implement proper database session management
    pass


# ==================== Order Execution Endpoints ====================

@router.post("/execute", response_model=ExecuteOrderResponse)
async def execute_order(
    request: ExecuteOrderRequest,
    executor: OrderExecutor = Depends(get_order_executor),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Execute a trade order.

    Process:
    1. Fetch account balance and open positions
    2. Run risk check
    3. Submit order to broker
    4. Save to database
    5. Return execution result
    """
    try:
        logger.info(f"Received order execution request: {request.symbol} {request.side.value}")

        # Get account balance from broker
        account_balance = 100000.0  # TODO: Fetch from actual broker based on asset_class

        # For now, skip database operations (no DB connected yet)
        # TODO: Implement proper database session management
        open_positions = []
        daily_trades = 0
        daily_pnl = 0.0

        # Execute order
        response = await executor.execute_order(
            order_request=request,
            account_balance=account_balance,
            open_positions=open_positions,
            daily_trades_count=daily_trades,
            daily_pnl=daily_pnl,
            perform_risk_check=True
        )

        # TODO: Save order to database if successful

        return response

    except Exception as e:
        import traceback
        logger.error(f"Order execution failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Order execution failed: {str(e)}"
        )


@router.post("/position-size", response_model=PositionSizeResponse)
async def calculate_position_size(
    request: PositionSizeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Calculate optimal position size based on risk parameters."""
    try:
        position_sizer = PositionSizer()

        # Get account balance if not provided
        account_balance = request.account_balance
        if not account_balance:
            # TODO: Fetch from broker
            account_balance = 10000.0

        # Calculate position size
        quantity, details = position_sizer.calculate_position_size(
            account_balance=account_balance,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            risk_per_trade_percent=request.risk_per_trade_percent,
            method=request.method,
            risk_multiplier=request.risk_multiplier
        )

        return PositionSizeResponse(
            success=True,
            quantity=quantity,
            position_value=details["position_value"],
            risk_amount=details["risk_amount"],
            risk_percent=details["risk_percent"],
            account_balance=details["account_balance"],
            entry_price=details["entry_price"],
            stop_loss_price=details["stop_loss_price"],
            stop_loss_distance=details["stop_loss_distance_pct"]
        )

    except Exception as e:
        logger.error(f"Position size calculation failed: {e}")
        return PositionSizeResponse(
            success=False,
            quantity=0.0,
            position_value=0.0,
            risk_amount=0.0,
            risk_percent=0.0,
            account_balance=request.account_balance or 0.0,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            stop_loss_distance=0.0,
            error_message=str(e)
        )


@router.post("/risk-check", response_model=RiskCheckResponse)
async def check_risk(
    request: RiskCheckRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """Validate risk before executing an order."""
    try:
        risk_manager = RiskManager()
        position_repo = PositionRepository(db)
        order_repo = OrderRepository(db)

        # Get account balance (mock for now)
        account_balance = 10000.0  # TODO: Fetch from broker

        # Get open positions
        open_positions_db = await position_repo.get_open_positions(request.user_id)
        open_positions = [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "entry_price": pos.avg_entry_price,
                "stop_loss_price": pos.stop_loss_price,
                "status": pos.status.value
            }
            for pos in open_positions_db
        ]

        # Get daily stats
        daily_trades = await order_repo.get_daily_trade_count(request.user_id)
        daily_pnl = await position_repo.get_daily_pnl(request.user_id)

        # Run risk check
        risk_result = await risk_manager.check_risk(
            user_id=request.user_id,
            symbol=request.symbol,
            side=request.side.value,
            quantity=request.quantity,
            entry_price=request.entry_price,
            stop_loss_price=request.stop_loss_price,
            account_balance=account_balance,
            open_positions=open_positions,
            daily_trades_count=daily_trades,
            daily_pnl=daily_pnl
        )

        return RiskCheckResponse(
            approved=risk_result.approved,
            risk_score=risk_result.risk_score,
            position_risk_percent=risk_result.metrics.get("position_risk_percent", 0.0),
            total_account_risk_percent=risk_result.metrics.get("total_account_risk_percent", 0.0),
            margin_usage_percent=risk_result.metrics.get("margin_usage_percent", 0.0),
            positions_count=risk_result.metrics.get("positions_count", 0),
            max_positions_allowed=risk_result.metrics.get("max_positions_allowed", 0),
            positions_in_symbol=risk_result.metrics.get("positions_in_symbol", 0),
            violations=risk_result.violations,
            warnings=risk_result.warnings
        )

    except Exception as e:
        logger.error(f"Risk check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk check failed: {str(e)}"
        )


# ==================== Positions & Account Endpoints ====================

@router.get("/positions/{user_id}", response_model=PositionsResponse)
async def get_positions(user_id: str):
    """
    Get all open positions from all brokers for a user.

    Fetches positions from both Alpaca and Binance and returns combined view.
    """
    try:
        logger.info(f"Fetching positions for user: {user_id}")

        # Import global broker clients
        from main import alpaca_client, binance_client

        all_positions = []
        total_value = 0.0
        total_pnl = 0.0

        # Fetch Alpaca positions
        if alpaca_client and alpaca_client.is_connected():
            try:
                alpaca_positions = await alpaca_client.get_all_positions()
                for pos in alpaca_positions:
                    pnl_percent = (pos.unrealized_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0.0
                    position_response = PositionResponse(
                        symbol=pos.symbol,
                        quantity=pos.quantity,
                        avg_entry_price=pos.avg_entry_price,
                        current_price=pos.current_price,
                        market_value=pos.market_value,
                        cost_basis=pos.cost_basis,
                        unrealized_pnl=pos.unrealized_pnl,
                        unrealized_pnl_percent=pnl_percent,
                        side=pos.side,
                        broker="alpaca"
                    )
                    all_positions.append(position_response)
                    total_value += pos.market_value
                    total_pnl += pos.unrealized_pnl
                logger.info(f"Found {len(alpaca_positions)} Alpaca positions")
            except Exception as e:
                logger.warning(f"Failed to fetch Alpaca positions: {e}")

        # Fetch Binance positions (disabled for now - too slow on testnet with many dust balances)
        # TODO: Re-enable with better caching or concurrent price fetching
        # if binance_client and binance_client.is_connected():
        #     try:
        #         binance_positions = await binance_client.get_all_positions()
        #         for pos in binance_positions:
        #             pnl_percent = (pos.unrealized_pnl / pos.cost_basis * 100) if pos.cost_basis > 0 else 0.0
        #             position_response = PositionResponse(
        #                 symbol=pos.symbol,
        #                 quantity=pos.quantity,
        #                 avg_entry_price=pos.avg_entry_price,
        #                 current_price=pos.current_price,
        #                 market_value=pos.market_value,
        #                 cost_basis=pos.cost_basis,
        #                 unrealized_pnl=pos.unrealized_pnl,
        #                 unrealized_pnl_percent=pnl_percent,
        #                 side=pos.side,
        #                 broker="binance"
        #             )
        #             all_positions.append(position_response)
        #             total_value += pos.market_value
        #             total_pnl += pos.unrealized_pnl
        #         logger.info(f"Found {len(binance_positions)} Binance positions")
        #     except Exception as e:
        #         logger.warning(f"Failed to fetch Binance positions: {e}")

        # Calculate total P&L percentage
        total_pnl_percent = (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0.0

        return PositionsResponse(
            success=True,
            positions=all_positions,
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            count=len(all_positions)
        )

    except Exception as e:
        logger.error(f"Failed to fetch positions: {e}")
        return PositionsResponse(
            success=False,
            error_message=str(e)
        )


@router.get("/account/{user_id}", response_model=AccountResponse)
async def get_account(user_id: str):
    """
    Get account information from all brokers for a user.

    Fetches account balance, equity, and buying power from connected brokers.
    """
    try:
        logger.info(f"Fetching account info for user: {user_id}")

        # Import global broker clients
        from main import alpaca_client, binance_client

        alpaca_cash = 0.0
        alpaca_equity = 0.0
        alpaca_buying_power = 0.0
        binance_usdt = 0.0
        binance_total = 0.0

        # Fetch Alpaca account data
        if alpaca_client and alpaca_client.is_connected():
            try:
                response = await alpaca_client.client.get(f"{alpaca_client.base_url}/v2/account")
                response.raise_for_status()
                account = response.json()

                alpaca_cash = float(account.get("cash", 0))
                alpaca_equity = float(account.get("equity", 0))
                alpaca_buying_power = float(account.get("buying_power", 0))

                logger.info(f"Alpaca: Cash=${alpaca_cash:.2f}, Equity=${alpaca_equity:.2f}")
            except Exception as e:
                logger.warning(f"Failed to fetch Alpaca account: {e}")

        # Fetch Binance account data
        if binance_client and binance_client.is_connected():
            try:
                import time
                params = {"timestamp": int(time.time() * 1000)}
                params["signature"] = binance_client._generate_signature(params)

                response = await binance_client.client.get(
                    f"{binance_client.base_url}/api/v3/account",
                    params=params
                )
                response.raise_for_status()
                account = response.json()

                # Calculate USDT balance
                for balance in account.get("balances", []):
                    if balance["asset"] == "USDT":
                        binance_usdt = float(balance["free"]) + float(balance["locked"])
                        binance_total = binance_usdt  # Simplified for now
                        break

                logger.info(f"Binance: USDT=${binance_usdt:.2f}")
            except Exception as e:
                logger.warning(f"Failed to fetch Binance account: {e}")

        # Calculate totals
        total_cash = alpaca_cash + binance_usdt
        total_equity = alpaca_equity + binance_total

        return AccountResponse(
            success=True,
            user_id=user_id,
            alpaca_cash=alpaca_cash,
            alpaca_equity=alpaca_equity,
            alpaca_buying_power=alpaca_buying_power,
            binance_usdt_balance=binance_usdt,
            binance_total_value=binance_total,
            total_cash=total_cash,
            total_equity=total_equity
        )

    except Exception as e:
        logger.error(f"Failed to fetch account info: {e}")
        return AccountResponse(
            success=False,
            user_id=user_id,
            error_message=str(e)
        )


@router.delete("/positions/{user_id}/{symbol}", response_model=ClosePositionResponse)
async def close_position(user_id: str, symbol: str, broker: str = "auto"):
    """
    Close a position for a symbol.

    Args:
        user_id: User ID
        symbol: Trading symbol
        broker: Broker to close position on (alpaca/binance/auto)
    """
    try:
        logger.info(f"Closing position {symbol} for user {user_id} on broker {broker}")

        # Import global broker clients
        from main import alpaca_client, binance_client

        # Determine which broker to use
        if broker == "auto":
            # Try to find which broker has this position
            if alpaca_client and alpaca_client.is_connected():
                position = await alpaca_client.get_position(symbol)
                if position:
                    broker = "alpaca"

            if broker == "auto" and binance_client and binance_client.is_connected():
                position = await binance_client.get_position(symbol)
                if position:
                    broker = "binance"

        # Close position on appropriate broker
        if broker == "alpaca":
            if not alpaca_client or not alpaca_client.is_connected():
                raise Exception("Alpaca client not connected")

            close_order = await alpaca_client.close_position(symbol)
            return ClosePositionResponse(
                success=True,
                symbol=symbol,
                broker="alpaca",
                order_id=close_order.broker_order_id,
                message=f"Position {symbol} closed successfully on Alpaca"
            )

        elif broker == "binance":
            if not binance_client or not binance_client.is_connected():
                raise Exception("Binance client not connected")

            close_order = await binance_client.close_position(symbol)
            return ClosePositionResponse(
                success=True,
                symbol=symbol,
                broker="binance",
                order_id=close_order.broker_order_id,
                message=f"Position {symbol} closed successfully on Binance"
            )

        else:
            raise Exception(f"Position {symbol} not found on any broker")

    except Exception as e:
        logger.error(f"Failed to close position {symbol}: {e}")
        return ClosePositionResponse(
            success=False,
            symbol=symbol,
            broker=broker,
            message="Failed to close position",
            error_message=str(e)
        )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check."""
    try:
        # Import global broker clients
        from main import alpaca_client, binance_client

        # Check actual broker connections
        alpaca_connected = alpaca_client.is_connected() if alpaca_client else False
        binance_connected = binance_client.is_connected() if binance_client else False
        database_connected = True  # Assume connected if endpoint works

        return HealthResponse(
            status="healthy",
            service="executor-service",
            version=settings.VERSION,
            timestamp=datetime.utcnow(),
            database_connected=database_connected,
            alpaca_connected=alpaca_connected,
            binance_connected=binance_connected
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service unhealthy: {str(e)}"
        )
