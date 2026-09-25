"""
Executor Service - Main Application
FastAPI application for order execution and position management
"""

import logging
import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.config import settings
from api import router
from brokers import AlpacaBrokerClient, BinanceBrokerClient
from order_manager import OrderExecutor
from position_sizer import PositionSizer
from risk_manager import RiskManager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)


# Global instances
alpaca_client: AlpacaBrokerClient = None
binance_client: BinanceBrokerClient = None
order_executor: OrderExecutor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup and shutdown events.
    """
    # ========== STARTUP ==========
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    global alpaca_client, binance_client, order_executor

    try:
        # Initialize broker clients
        if settings.ALPACA_API_KEY and settings.ALPACA_API_SECRET:
            logger.info("Initializing Alpaca broker client...")
            alpaca_client = AlpacaBrokerClient(
                api_key=settings.ALPACA_API_KEY,
                api_secret=settings.ALPACA_API_SECRET,
                base_url=settings.ALPACA_BASE_URL
            )
            await alpaca_client.connect()
            logger.info("✅ Alpaca client connected")
        else:
            logger.warning("Alpaca credentials not provided, skipping initialization")

        if settings.BINANCE_API_KEY and settings.BINANCE_API_SECRET:
            logger.info("Initializing Binance broker client...")
            binance_client = BinanceBrokerClient(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_API_SECRET,
                base_url=settings.BINANCE_BASE_URL
            )
            await binance_client.connect()
            logger.info("✅ Binance client connected")
        else:
            logger.warning("Binance credentials not provided, skipping initialization")

        # Initialize order executor
        logger.info("Initializing order executor...")
        order_executor = OrderExecutor(
            alpaca_client=alpaca_client,
            binance_client=binance_client,
            position_sizer=PositionSizer(),
            risk_manager=RiskManager(
                max_risk_per_trade_percent=settings.MAX_RISK_PER_TRADE_PERCENT,
                max_account_risk_percent=settings.MAX_ACCOUNT_RISK_PERCENT,
                max_positions_per_symbol=settings.MAX_POSITIONS_PER_SYMBOL,
                max_total_positions=settings.MAX_TOTAL_POSITIONS,
                max_daily_loss_percent=settings.MAX_DAILY_LOSS_PERCENT,
                max_daily_trades=settings.MAX_DAILY_TRADES,
                min_account_balance=settings.MIN_ACCOUNT_BALANCE,
                margin_usage_limit_percent=settings.MARGIN_USAGE_LIMIT_PERCENT,
                emergency_shutdown_loss_percent=settings.EMERGENCY_SHUTDOWN_LOSS_PERCENT
            )
        )
        logger.info("✅ Order executor initialized")

        # Set global executor in routes module
        import api.routes as api_routes
        api_routes.set_order_executor(order_executor)

        logger.info(f"🚀 {settings.APP_NAME} started successfully on {settings.HOST}:{settings.PORT}")

        yield

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    # ========== SHUTDOWN ==========
    logger.info("Shutting down Executor Service...")

    try:
        # Disconnect broker clients
        if alpaca_client:
            await alpaca_client.disconnect()
            logger.info("✅ Alpaca client disconnected")

        if binance_client:
            await binance_client.disconnect()
            logger.info("✅ Binance client disconnected")

        logger.info("✅ Executor Service shut down successfully")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Order execution service for Terminal AI Trading System",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/status")
async def status():
    """Service status endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "brokers": {
            "alpaca": {
                "configured": bool(settings.ALPACA_API_KEY),
                "connected": alpaca_client.is_connected() if alpaca_client else False
            },
            "binance": {
                "configured": bool(settings.BINANCE_API_KEY),
                "connected": binance_client.is_connected() if binance_client else False
            }
        },
        "features": {
            "paper_trading": settings.ENABLE_PAPER_TRADING,
            "live_trading": settings.ENABLE_LIVE_TRADING,
            "dry_run": settings.DRY_RUN_MODE
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
