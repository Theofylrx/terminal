"""
Terminal Trading System - API Gateway
Entry point for all client requests
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from gateway.config.settings import settings
from gateway.routes import proxy, websocket
from gateway.middleware.logging import RequestLoggingMiddleware
from gateway.middleware.rate_limiter import get_rate_limit_info

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup and shutdown events.
    """
    # Startup
    logger.info("🚀 API Gateway starting...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Rate limiting: {'enabled' if settings.RATE_LIMIT_ENABLED else 'disabled'}")

    yield

    # Shutdown
    logger.info("🛑 API Gateway shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="API Gateway for Terminal Trading System",
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# ==================== MIDDLEWARE ====================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


# ==================== ERROR HANDLERS ====================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


# ==================== ROUTES ====================

# Health check
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    Returns gateway status and version.
    """
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }


# Readiness check (for Kubernetes)
@app.get("/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint.
    Checks if gateway can accept traffic.
    """
    # In production, check connectivity to:
    # - Redis
    # - Database
    # - Critical microservices
    return {"status": "ready"}


# Liveness check (for Kubernetes)
@app.get("/alive", tags=["health"])
async def liveness_check():
    """
    Liveness check endpoint.
    Checks if gateway is running.
    """
    return {"status": "alive"}


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs" if settings.DEBUG else "disabled",
        "health": "/health",
        "websocket": "/ws"
    }


# Include routers
app.include_router(proxy.router, tags=["proxy"])
app.include_router(websocket.router, tags=["websocket"])


# ==================== RESPONSE MIDDLEWARE ====================

@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    """
    Add custom headers to all responses.
    """
    response = await call_next(request)

    # Add rate limit headers
    if hasattr(request.state, "rate_limit_remaining"):
        rate_limit_headers = get_rate_limit_info(request)
        for key, value in rate_limit_headers.items():
            response.headers[key] = value

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"

    return response


# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )
