"""
Service Proxy Router
Routes requests to backend microservices
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
import httpx
from gateway.config.settings import settings
from gateway.middleware.auth import get_current_user, get_current_user_optional
from gateway.middleware.rate_limiter import rate_limit_check

router = APIRouter()


async def proxy_request(
    request: Request,
    service_url: str,
    path: str,
    user: Optional[Dict[str, Any]] = None
) -> Response:
    """
    Proxy HTTP request to a microservice.

    Args:
        request: Incoming FastAPI request
        service_url: Target service base URL
        path: Path to append to service URL
        user: Authenticated user data (optional)

    Returns:
        Response from microservice

    Raises:
        HTTPException: On service errors or timeouts
    """
    # Build target URL
    target_url = f"{service_url}{path}"

    # Prepare headers (forward most headers, add custom ones)
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove host header

    # Add user context if authenticated
    if user:
        headers["X-User-ID"] = user.get("sub", "")
        headers["X-User-Email"] = user.get("email", "")

    # Add request ID for tracing
    headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")

    # Get request body
    body = await request.body()

    # Make request to microservice
    async with httpx.AsyncClient(timeout=settings.SERVICE_TIMEOUT) as client:
        try:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
                follow_redirects=False
            )

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Service timeout: {service_url}"
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service unavailable: {service_url}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gateway error: {str(e)}"
            )


# ==================== AUTH SERVICE ROUTES ====================

@router.api_route(
    "/api/v1/auth/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def auth_service_proxy(
    path: str,
    request: Request,
    user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Proxy requests to Auth Service.
    Public endpoints: /login, /register
    Protected endpoints: require authentication
    """
    await rate_limit_check(request)
    return await proxy_request(
        request,
        settings.AUTH_SERVICE_URL,
        f"/{path}",
        user
    )


# ==================== TRADING SERVICE ROUTES ====================

@router.api_route(
    "/api/v1/positions/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
@router.api_route(
    "/api/v1/orders/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
@router.api_route(
    "/api/v1/portfolio/{path:path}",
    methods=["GET"]
)
async def trading_service_proxy(
    path: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """
    Proxy requests to Trading Service.
    All endpoints require authentication.
    """
    await rate_limit_check(request, max_requests=100)  # Higher limit for trading
    return await proxy_request(
        request,
        settings.TRADING_SERVICE_URL,
        f"/{path}",
        user
    )


# ==================== ANALYTICS SERVICE ROUTES ====================

@router.api_route(
    "/api/v1/analytics/{path:path}",
    methods=["GET", "POST"]
)
@router.api_route(
    "/api/v1/performance/{path:path}",
    methods=["GET"]
)
@router.api_route(
    "/api/v1/reports/{path:path}",
    methods=["GET", "POST"]
)
async def analytics_service_proxy(
    path: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """
    Proxy requests to Analytics Service.
    All endpoints require authentication.
    """
    await rate_limit_check(request)
    return await proxy_request(
        request,
        settings.ANALYTICS_SERVICE_URL,
        f"/{path}",
        user
    )


# ==================== STRATEGY SERVICE ROUTES ====================

@router.api_route(
    "/api/v1/strategies/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
@router.api_route(
    "/api/v1/configs/{path:path}",
    methods=["GET", "PUT", "PATCH"]
)
async def strategy_service_proxy(
    path: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """
    Proxy requests to Strategy Service.
    All endpoints require authentication.
    """
    await rate_limit_check(request)
    return await proxy_request(
        request,
        settings.STRATEGY_SERVICE_URL,
        f"/{path}",
        user
    )


# ==================== NOTIFICATION SERVICE ROUTES ====================

@router.api_route(
    "/api/v1/notifications/{path:path}",
    methods=["GET", "POST", "PUT", "DELETE"]
)
async def notification_service_proxy(
    path: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    """
    Proxy requests to Notification Service.
    All endpoints require authentication.
    """
    await rate_limit_check(request)
    return await proxy_request(
        request,
        settings.NOTIFICATION_SERVICE_URL,
        f"/{path}",
        user
    )
