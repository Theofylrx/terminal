"""
Market Data Service - Main Application

Collects real-time market data from multiple brokers (Alpaca, Binance, OANDA),
stores in TimescaleDB, and distributes via WebSocket and Redis events.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

# Add shared to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.connection import init_db, get_session_maker
from shared.events.event_bus import EventPublisher, get_redis_client

from .core.config import settings
from .services.market_data_service import MarketDataService
from .api.routes import router, set_market_data_service


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Global service instance
market_data_service: MarketDataService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    global market_data_service

    logger.info("🚀 Market Data Service starting...")

    try:
        # Initialize database
        await init_db(settings.DATABASE_URL)
        logger.info("✅ Database initialized")

        # Initialize Redis
        redis_client = await get_redis_client(settings.REDIS_URL)
        logger.info("✅ Redis connected")

        # Initialize event publisher
        event_publisher = EventPublisher(redis_client, settings.REDIS_STREAM_MAXLEN)

        # Initialize database session
        session_maker = get_session_maker()

        async with session_maker() as session:
            # Initialize Market Data Service
            market_data_service = MarketDataService(
                session=session,
                event_publisher=event_publisher,
            )

            # Set service in routes
            set_market_data_service(market_data_service)

            # Start connectors
            await market_data_service.start()

            logger.info("✅ Market Data Service started successfully")
            logger.info(f"📊 Service status: {market_data_service.get_status()}")

            yield

    except Exception as e:
        logger.error(f"Failed to start Market Data Service: {e}")
        raise

    finally:
        # Shutdown
        logger.info("🛑 Market Data Service shutting down...")

        if market_data_service:
            await market_data_service.stop()

        logger.info("✅ Market Data Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Market Data Service",
    description="Real-time market data collection and distribution",
    version="1.0.0",
    lifespan=lifespan,
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
app.include_router(router, prefix="/api/v1", tags=["market-data"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Market Data Service",
        "version": "1.0.0",
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
