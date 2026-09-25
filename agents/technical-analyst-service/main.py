"""
Technical Analyst Service - Main Application

Analyzes market data using technical indicators and pattern detection
to generate trading signals with confidence scores.
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

from shared.database.connection import init_db

from .core.config import settings
from .api.routes import router
from .api.auth_routes import router as auth_router


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    logger.info("🚀 Technical Analyst Service starting...")

    try:
        # Initialize database (init_db is not async)
        init_db(settings.DATABASE_URL)
        logger.info("✅ Database initialized")

        logger.info("✅ Technical Analyst Service started successfully")

        yield

    except Exception as e:
        logger.error(f"Failed to start Technical Analyst Service: {e}")
        raise

    finally:
        logger.info("🛑 Technical Analyst Service shutting down...")
        logger.info("✅ Technical Analyst Service stopped")


# Create FastAPI app
app = FastAPI(
    title="Technical Analyst Service",
    description="""
## Technical Analysis & Signal Generation Service

Enterprise-grade technical analysis service providing institutional-quality trading signals.

### Features

#### Technical Indicators (15 indicators)
- **Trend**: EMA, SMA, MACD
- **Momentum**: RSI, Stochastic, ROC
- **Volatility**: Bollinger Bands, ATR, Standard Deviation
- **Volume**: OBV, Volume SMA, VWAP

#### Pattern Detection (10+ patterns)
- **Candlestick Patterns**: Doji, Hammer, Shooting Star, Engulfing, Morning/Evening Star
- **Chart Patterns**: Head & Shoulders, Double Top/Bottom, Triangles

#### Advanced Institutional Patterns

**Elliott Wave Analysis**
- 5-wave impulse patterns with Fibonacci levels
- Wave validation following Elliott Wave Theory rules
- Fibonacci retracements (38.2%, 50%, 61.8%, 78.6%)
- Fibonacci extensions (100%, 161.8%, 261.8%)

**RSI Divergence Detection**
- Regular Bullish/Bearish divergence (reversal signals)
- Hidden Bullish/Bearish divergence (continuation signals)
- Break of Structure (BOS) confirmation
- Supply/Demand zone integration

**Smart Money Concepts (SMC)**
- Break of Structure (BOS) detection
- Change of Character (CHoCH) identification
- Fair Value Gaps (FVG) - price imbalances
- Supply/Demand zones
- Order blocks
- Premium/Discount zones

### Signal Generation
Combines all indicators and patterns to generate high-confidence trading signals with:
- Entry price and confidence score
- Target price and stop loss levels
- Risk/reward ratio
- Detailed reasoning with pattern confluence
- Multi-timeframe support

### Endpoints
- **Signals**: Generate and retrieve trading signals
- **Indicators**: Get technical indicator values
- **Elliott Wave**: Detect Elliott Wave patterns
- **Divergences**: Detect RSI divergences
- **Smart Money**: Detect institutional patterns
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and service status"
        },
        {
            "name": "auth",
            "description": "User authentication (login, register, profile)"
        },
        {
            "name": "signals",
            "description": "Trading signal generation and retrieval"
        },
        {
            "name": "indicators",
            "description": "Technical indicator calculations"
        },
        {
            "name": "elliott-wave",
            "description": "Elliott Wave pattern detection with Fibonacci levels"
        },
        {
            "name": "divergences",
            "description": "RSI divergence detection with Break of Structure confirmation"
        },
        {
            "name": "smart-money",
            "description": "Smart Money Concepts (BOS, FVG, Supply/Demand)"
        },
    ],
    contact={
        "name": "Terminal Development Team",
        "email": "dev@terminal.ai",
    },
    license_info={
        "name": "Proprietary",
    },
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
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(router, prefix="/api/v1", tags=["technical-analyst"])

# Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Technical Analyst Service",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check for Docker."""
    return {
        "status": "healthy",
        "service": "technical-analyst-service",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    # Get port from environment or use default
    import os
    port = int(os.getenv("SERVICE_PORT", "8004"))

    uvicorn.run(
        "agents.technical-analyst-service.main:app",
        host="0.0.0.0",
        port=port,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
