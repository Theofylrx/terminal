"""
Terminal Trading System - Auto-Trading Engine
Autonomous trading orchestration service
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.connection import init_db, close_db
from .core.config import settings
from .workers.symbol_monitor import SymbolMonitorWorker
from .workers.position_monitor import PositionMonitorWorker
from .workers.session_manager import SessionManagerWorker

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("auto-trading-engine")

# Global worker instances
symbol_monitor: SymbolMonitorWorker = None
position_monitor: PositionMonitorWorker = None
session_manager: SessionManagerWorker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global symbol_monitor, position_monitor, session_manager

    # Startup
    logger.info("🤖 Auto-Trading Engine starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    try:
        init_db(settings.DATABASE_URL)
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    # Initialize and start background workers
    try:
        logger.info("🔄 Starting background workers...")

        # Symbol Monitor Worker
        symbol_monitor = SymbolMonitorWorker()
        asyncio.create_task(symbol_monitor.start())
        logger.info("✅ Symbol Monitor Worker started")

        # Position Monitor Worker
        position_monitor = PositionMonitorWorker()
        asyncio.create_task(position_monitor.start())
        logger.info("✅ Position Monitor Worker started")

        # Session Manager Worker
        session_manager = SessionManagerWorker()
        asyncio.create_task(session_manager.start())
        logger.info("✅ Session Manager Worker started")

        logger.info("🚀 All workers operational - Auto-Trading Engine ready!")

    except Exception as e:
        logger.error(f"❌ Failed to start workers: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Auto-Trading Engine shutting down...")

    # Stop workers
    if symbol_monitor:
        await symbol_monitor.stop()
        logger.info("✅ Symbol Monitor Worker stopped")

    if position_monitor:
        await position_monitor.stop()
        logger.info("✅ Position Monitor Worker stopped")

    if session_manager:
        await session_manager.stop()
        logger.info("✅ Session Manager Worker stopped")

    # Close database
    await close_db()
    logger.info("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Autonomous trading orchestration for Terminal Trading System",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
if settings.ENABLE_PROMETHEUS_METRICS:
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Include API routers
from .api.routes import config
app.include_router(config.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "workers": {
            "symbol_monitor": "running" if symbol_monitor and symbol_monitor.running else "stopped",
            "position_monitor": "running" if position_monitor and position_monitor.running else "stopped",
            "session_manager": "running" if session_manager and session_manager.running else "stopped"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    workers_healthy = all([
        symbol_monitor and symbol_monitor.running,
        position_monitor and position_monitor.running,
        session_manager and session_manager.running
    ])

    return {
        "status": "healthy" if workers_healthy else "degraded",
        "service": "auto-trading-engine",
        "version": settings.VERSION,
        "workers": {
            "symbol_monitor": symbol_monitor.running if symbol_monitor else False,
            "position_monitor": position_monitor.running if position_monitor else False,
            "session_manager": session_manager.running if session_manager else False
        }
    }


@app.get("/workers/status")
async def workers_status():
    """Get detailed worker status."""
    return {
        "symbol_monitor": {
            "running": symbol_monitor.running if symbol_monitor else False,
            "interval_seconds": settings.SYMBOL_MONITOR_INTERVAL_SECONDS,
            "stats": symbol_monitor.get_stats() if symbol_monitor else {}
        },
        "position_monitor": {
            "running": position_monitor.running if position_monitor else False,
            "interval_seconds": settings.POSITION_MONITOR_INTERVAL_SECONDS,
            "stats": position_monitor.get_stats() if position_monitor else {}
        },
        "session_manager": {
            "running": session_manager.running if session_manager else False,
            "interval_seconds": settings.SESSION_MANAGER_INTERVAL_SECONDS,
            "stats": session_manager.get_stats() if session_manager else {}
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
