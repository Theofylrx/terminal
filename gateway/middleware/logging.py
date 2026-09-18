"""
Request Logging Middleware
Logs all incoming requests and responses
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging

# Configure logger
logger = logging.getLogger("gateway")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    Includes timing, status codes, and request details.
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process each request and log details.

        Args:
            request: Incoming request
            call_next: Next middleware/route handler

        Returns:
            Response from downstream handlers
        """
        # Generate request ID
        request_id = generate_request_id()
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        log_request(request, request_id)

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            log_response(request, response, duration, request_id)

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{duration:.4f}s"

            return response

        except Exception as e:
            duration = time.time() - start_time
            log_error(request, e, duration, request_id)
            raise


def generate_request_id() -> str:
    """Generate unique request ID."""
    import uuid
    return str(uuid.uuid4())[:8]


def log_request(request: Request, request_id: str) -> None:
    """Log incoming request details."""
    logger.info(
        "Incoming request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )


def log_response(
    request: Request,
    response: Response,
    duration: float,
    request_id: str
) -> None:
    """Log response details."""
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration": f"{duration:.4f}s",
        }
    )


def log_error(
    request: Request,
    error: Exception,
    duration: float,
    request_id: str
) -> None:
    """Log request error."""
    logger.error(
        "Request failed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "error": str(error),
            "error_type": type(error).__name__,
            "duration": f"{duration:.4f}s",
        },
        exc_info=True
    )
