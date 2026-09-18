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
        # Initialize database
        await init_db(settings.DATABASE_URL)
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
    description="Technical analysis and signal generation service",
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
