"""
Terminal Trading System - Auth Service
User authentication and authorization service
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

import sys
sys.path.append('/app')

from shared.database.connection import init_db, close_db
from services.auth_service.core.config import settings
from services.auth_service.api.routes import auth

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info("🔐 Auth Service starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database
    try:
        init_db(settings.DATABASE_URL)
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Auth Service shutting down...")
    await close_db()
    logger.info("✅ Database connection closed")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Authentication and authorization service for Terminal Trading System",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# ==================== MIDDLEWARE ====================

# CORS (allow gateway to call this service)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to gateway URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ==================== ROUTES ====================

# Include auth routes
app.include_router(auth.router)


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint with service information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "docs": "/docs" if settings.DEBUG else "disabled"
    }


# Health check
@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    """
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
