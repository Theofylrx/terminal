"""
Rate Limiting Middleware
Prevents API abuse by limiting request rates
"""

import time
from typing import Optional
from fastapi import Request, HTTPException, status
from redis import Redis
from gateway.config.settings import settings

# Redis client for rate limiting
_redis_client: Optional[Redis] = None


def get_redis_client() -> Redis:
    """Get or create Redis client for rate limiting."""
    global _redis_client

    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5
        )

    return _redis_client


async def rate_limit_check(
    request: Request,
    max_requests: int = settings.RATE_LIMIT_PER_MINUTE,
    window_seconds: int = 60
) -> None:
    """
    Check if request should be rate limited.

    Args:
        request: FastAPI request object
        max_requests: Maximum requests allowed in the time window
        window_seconds: Time window in seconds

    Raises:
        HTTPException: If rate limit exceeded

    Example:
        @app.get("/endpoint")
        async def endpoint(request: Request):
            await rate_limit_check(request)
            return {"message": "Success"}
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    # Get client identifier (IP address or user ID)
    client_id = get_client_identifier(request)

    # Redis key for this client
    key = f"rate_limit:{client_id}"

    try:
        redis = get_redis_client()

        # Get current request count
        current_count = redis.get(key)

        if current_count is None:
            # First request in this window
            redis.setex(key, window_seconds, 1)
            return

        count = int(current_count)

        if count >= max_requests:
            # Rate limit exceeded
            ttl = redis.ttl(key)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + ttl),
                    "Retry-After": str(ttl)
                }
            )

        # Increment counter
        redis.incr(key)

        # Add rate limit headers to response
        request.state.rate_limit_remaining = max_requests - count - 1
        request.state.rate_limit_limit = max_requests

    except HTTPException:
        raise
    except Exception as e:
        # If Redis is down, log error but don't block requests
        print(f"Rate limiting error: {e}")
        # In production, you might want to fail closed (block requests)
        # or use an in-memory fallback
        pass


def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for rate limiting.
    Uses user ID if authenticated, otherwise IP address.

    Args:
        request: FastAPI request object

    Returns:
        Client identifier string
    """
    # If user is authenticated, use user ID
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.get('sub')}"

    # Otherwise use IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take first IP if multiple proxies
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


def get_rate_limit_info(request: Request) -> dict:
    """
    Get rate limit information to add to response headers.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with rate limit info
    """
    return {
        "X-RateLimit-Limit": str(getattr(request.state, "rate_limit_limit", settings.RATE_LIMIT_PER_MINUTE)),
        "X-RateLimit-Remaining": str(getattr(request.state, "rate_limit_remaining", settings.RATE_LIMIT_PER_MINUTE)),
    }
