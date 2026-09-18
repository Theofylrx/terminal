# API Gateway

Enterprise-grade API Gateway for Terminal Trading System.

## Features

### ✅ Authentication & Authorization
- JWT token validation
- User extraction from tokens
- Role-based access control (user, superuser)
- Optional authentication support

### ✅ Rate Limiting
- Redis-based distributed rate limiting
- Per-user and per-IP tracking
- Configurable limits per endpoint
- Rate limit headers in responses

### ✅ Request Routing
- Proxy to microservices (Auth, Trading, Analytics, Strategy, Notification)
- Service discovery via environment variables
- Automatic header forwarding
- User context propagation

### ✅ WebSocket Support
- Real-time updates for positions, orders, prices
- JWT authentication for WebSocket connections
- Connection management with automatic reconnection
- Broadcast and targeted messaging

### ✅ Monitoring
- Prometheus metrics endpoint (`/metrics`)
- Request/response logging
- Performance timing
- Health checks (`/health`, `/ready`, `/alive`)

### ✅ Security
- CORS configuration
- Security headers (X-Frame-Options, X-XSS-Protection, etc.)
- Request ID tracking
- Non-root Docker user

## Architecture

```
Client Request
      ↓
[ CORS Middleware ]
      ↓
[ Request Logging ]
      ↓
[ Rate Limiting ]
      ↓
[ JWT Authentication ]
      ↓
[ Route to Service ]
      ↓
Backend Microservice
```

## Endpoints

### Health Checks
- `GET /health` - Health status
- `GET /ready` - Readiness check (Kubernetes)
- `GET /alive` - Liveness check (Kubernetes)
- `GET /metrics` - Prometheus metrics

### Authentication (→ Auth Service)
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Trading (→ Trading Service) [Protected]
- `GET /api/v1/positions` - List positions
- `POST /api/v1/orders` - Create order
- `GET /api/v1/portfolio` - Portfolio summary

### Analytics (→ Analytics Service) [Protected]
- `GET /api/v1/analytics/performance` - Performance metrics
- `GET /api/v1/reports` - Generate reports

### Strategies (→ Strategy Service) [Protected]
- `GET /api/v1/strategies` - List strategies
- `PUT /api/v1/configs/:id` - Update strategy config

### WebSocket
- `WS /ws?token=<jwt>` - Real-time updates

## Configuration

Environment variables (see `.env.example`):

```bash
# Security
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/db

# Redis
REDIS_URL=redis://redis:6379/0

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_ENABLED=true

# Service URLs
AUTH_SERVICE_URL=http://auth-service:8000
TRADING_SERVICE_URL=http://trading-service:8000
# ...
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql+asyncpg://...
export REDIS_URL=redis://...
export JWT_SECRET=your_secret

# Run gateway
python -m uvicorn gateway.main:app --reload --port 8080
```

## Running with Docker

```bash
# Build and start
docker-compose up gateway

# Access
curl http://localhost:8080/health
```

## Development

### Adding New Routes

1. Create route handler in `routes/proxy.py`:

```python
@router.api_route("/api/v1/newservice/{path:path}", methods=["GET", "POST"])
async def new_service_proxy(
    path: str,
    request: Request,
    user: Dict = Depends(get_current_user)
):
    await rate_limit_check(request)
    return await proxy_request(
        request,
        settings.NEW_SERVICE_URL,
        f"/{path}",
        user
    )
```

2. Add service URL to `config/settings.py`:

```python
NEW_SERVICE_URL: str = "http://new-service:8000"
```

3. Update docker-compose.yml with environment variable

### Custom Middleware

Create middleware in `middleware/` directory:

```python
from starlette.middleware.base import BaseHTTPMiddleware

class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Before request
        response = await call_next(request)
        # After request
        return response
```

Add to `main.py`:

```python
app.add_middleware(CustomMiddleware)
```

## Testing

```bash
# Health check
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics

# Protected endpoint (requires JWT)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8080/api/v1/positions

# WebSocket (requires JWT)
wscat -c "ws://localhost:8080/ws?token=<token>"
```

## Monitoring

### Prometheus Metrics

Available at `/metrics`:
- Request count
- Request duration
- Active requests
- Response status codes

### Grafana Dashboard

Import dashboard from `infrastructure/monitoring/grafana/dashboards/gateway-dashboard.json`

## Performance

- Async/await throughout (non-blocking)
- Connection pooling for database and Redis
- HTTP/2 support
- Configurable timeouts
- Circuit breaker pattern (coming soon)

## Security

- JWT token validation
- Rate limiting (prevent DDoS)
- CORS protection
- Security headers
- Request sanitization
- No hardcoded secrets
- Non-root Docker user

## Troubleshooting

### Gateway not starting
- Check DATABASE_URL and REDIS_URL
- Verify JWT_SECRET is set
- Check service URL environment variables

### 503 Service Unavailable
- Backend service is down
- Check `docker-compose ps`
- Check service logs: `docker-compose logs <service>`

### 429 Too Many Requests
- Rate limit exceeded
- Wait for rate limit window to reset
- Check `X-RateLimit-Reset` header

### WebSocket connection fails
- Invalid or expired JWT token
- Check token in query parameter: `/ws?token=<jwt>`

## License

MIT
