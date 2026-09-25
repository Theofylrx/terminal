# Terminal AI Trading System - Complete Workflow & Architecture

**Last Updated:** 2026-09-20
**Version:** 1.0.0
**Status:** Production Ready

---

## 🏗️ **System Architecture Overview**

The Terminal is a **cloud-native, microservices-based AI trading platform** designed for real-time market analysis and automated trading across multiple asset classes (stocks, crypto, forex).

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TERMINAL TRADING SYSTEM                          │
│                     (Microservices Architecture)                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  React Dashboard (Port 3000)                                            │
│  ├─ Real-time Market Data Visualization                                 │
│  ├─ Portfolio Management Interface                                      │
│  ├─ Trading Controls & Order Management                                 │
│  └─ System Monitoring Dashboard                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (Port 8080)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ├─ Request Routing & Load Balancing                                    │
│  ├─ JWT Authentication & Authorization                                  │
│  ├─ Rate Limiting & API Throttling                                      │
│  ├─ Request/Response Transformation                                     │
│  └─ Centralized Logging & Metrics Collection                            │
└─────────────────────────────────────────────────────────────────────────┘
                    ↓               ↓               ↓
    ┌───────────────────┬───────────────────┬───────────────────┐
    │                   │                   │                   │
┌───▼────────┐  ┌───────▼──────┐  ┌────────▼────┐  ┌──────────▼─────┐
│   Auth     │  │   Trading    │  │ Market Data │  │  Technical     │
│  Service   │  │   Service    │  │   Service   │  │   Analyst      │
│ (Port 8001)│  │ (Port 8002)  │  │ (Port 8003) │  │  (Port 8004)   │
└────────────┘  └──────────────┘  └─────────────┘  └────────────────┘
                                           ↓
                                  ┌────────────────┐
                                  │ WebSocket Feed │
                                  │  Alpaca + B

inance │
                                  └────────────────┘
         ↓                ↓                ↓                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                │
├─────────────────────────────────────────────────────────────────────────┤
│  PostgreSQL          Redis           RabbitMQ        Prometheus/Grafana │
│  (TimescaleDB)   (Cache/Events)   (Message Queue)    (Monitoring)       │
│  Port: 5432        Port: 6379       Port: 5672       Ports: 9090/3001   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 **Complete Data Flow - User Places Trade**

Let's walk through a complete trading workflow from start to finish:

### **Step 1: User Authentication**

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│   Frontend  │ ──1───→ │   Gateway   │ ──2───→ │    Auth     │
│             │         │             │         │   Service   │
│             │ ←──5──  │             │ ←──4──  │             │
└─────────────┘         └─────────────┘         └─────────────┘
                                                       ↓ 3
                                                ┌─────────────┐
                                                │  PostgreSQL │
                                                │  (Users DB) │
                                                └─────────────┘

1. User submits login credentials (email + password)
2. Gateway forwards to Auth Service
3. Auth Service:
   - Queries PostgreSQL for user
   - Verifies bcrypt password hash
   - Checks if account is active
4. Returns JWT tokens (access + refresh)
5. Gateway returns tokens to frontend
```

**Code Flow:**
```python
# Frontend
POST /auth/login
{
  "email": "trader@example.com",
  "password": "SecurePass123"
}

# Auth Service (services/auth-service/services/auth_service.py)
async def login(email, password):
    # 1. Authenticate user
    user = await authenticate_user(email, password)

    # 2. Generate JWT tokens
    access_token = create_access_token({
        "sub": user.id,
        "email": user.email,
        "username": user.username
    })

    refresh_token = create_refresh_token({"sub": user.id})

    # 3. Return tokens + user info
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {...}
    }
```

---

### **Step 2: Real-Time Market Data Streaming**

```
┌──────────────┐                  ┌──────────────────┐
│   Alpaca     │ ═══WebSocket═══→ │  Market Data     │
│   (Stocks)   │                  │     Service      │
└──────────────┘                  │                  │
                                  │  - Receives ticks│
┌──────────────┐                  │  - Normalizes    │───→ PostgreSQL
│   Binance    │ ═══WebSocket═══→ │  - Aggregates    │     (TimescaleDB)
│   (Crypto)   │                  │  - Broadcasts    │
└──────────────┘                  └──────────────────┘
                                           │
                                           ├───→ Redis (PubSub)
                                           │
                                           └───→ WebSocket Clients
                                                 (Frontend)
```

**Market Data Service Components:**

1. **Connectors** (`agents/market-data-service/collectors/`)
   - `alpaca.py` - Connects to Alpaca WebSocket (`wss://stream.data.alpaca.markets/v2/iex`)
   - `binance.py` - Connects to Binance WebSocket
   - Each connector handles:
     - Authentication
     - Subscription management
     - Reconnection logic
     - Error handling

2. **Data Processing** (`agents/market-data-service/processors/`)
   - Normalize tick data from different sources
   - Calculate OHLCV (Open, High, Low, Close, Volume) bars
   - Aggregate tick data into time windows (1m, 5m, 15m, 1h, 4h, 1d)

3. **Storage** (`agents/market-data-service/repositories/`)
   - Store ticks in TimescaleDB hypertables (optimized for time-series)
   - Create continuous aggregates for faster queries
   - Maintain data retention policies

4. **Broadcasting**
   - Publish to Redis channels for real-time distribution
   - Push to WebSocket clients
   - Trigger event bus notifications

**Code Example:**
```python
# agents/market-data-service/collectors/base/alpaca.py
async def handle_message(self, message):
    """Process incoming Alpaca WebSocket message"""

    # 1. Parse message
    if message['T'] == 't':  # Trade tick
        tick = {
            'symbol': message['S'],
            'price': message['p'],
            'volume': message['s'],
            'timestamp': message['t']
        }

        # 2. Store in database
        await self.tick_repository.create_tick(tick)

        # 3. Publish to Redis
        await self.event_publisher.publish(
            channel=f"market.{tick['symbol']}.tick",
            data=tick
        )

        # 4. Broadcast to WebSocket clients
        await self.websocket_manager.broadcast(
            f"market:{tick['symbol']}",
            tick
        )
```

---

### **Step 3: User Places Trade Order**

```
┌──────────┐    ┌─────────┐    ┌──────────┐    ┌────────────┐
│ Frontend │───→│ Gateway │───→│ Trading  │───→│ PostgreSQL │
│          │    │  (JWT)  │    │ Service  │    │ (Orders)   │
│          │    │         │    │          │    │            │
│          │    │         │    │    ↓     │    │            │
│          │    │         │    │  Validate│    │            │
│          │    │         │    │  Capital │    │            │
│          │    │         │    │   Check  │    │            │
│          │←───│         │←───│          │    │            │
└──────────┘    └─────────┘    └──────────┘    └────────────┘
                                      │
                                      ↓
                               ┌──────────────┐
                               │   RabbitMQ   │
                               │ (Order Queue)│
                               └──────────────┘
                                      │
                                      ↓
                               ┌──────────────┐
                               │ Order        │
                               │ Executor     │
                               └──────────────┘
```

**Trading Service Workflow:**

1. **Order Validation**
```python
# services/trading-service/services/order_service.py
async def create_order(user_id, order_request):
    # 1. Validate request
    if order_request.quantity <= 0:
        raise HTTPException(400, "Invalid quantity")

    # 2. Check user has sufficient capital
    user_capital = await get_user_capital(user_id)
    order_cost = order_request.quantity * order_request.price

    if order_cost > user_capital:
        raise HTTPException(400, "Insufficient funds")

    # 3. Create order in database
    order = await order_repository.create({
        'user_id': user_id,
        'symbol': order_request.symbol,
        'side': order_request.side,  # BUY or SELL
        'type': order_request.type,  # MARKET, LIMIT, STOP
        'quantity': order_request.quantity,
        'price': order_request.price,
        'status': 'PENDING'
    })

    # 4. Publish to order execution queue
    await message_queue.publish(
        exchange='orders',
        routing_key='new_order',
        message=order
    )

    # 5. Emit event
    await event_publisher.publish(
        event_type='ORDER_CREATED',
        data=order
    )

    return order
```

2. **Position Management**
```python
# services/trading-service/services/position_service.py
async def open_position(user_id, symbol, side, quantity, entry_price):
    """Open a new trading position"""

    position = await position_repository.create({
        'user_id': user_id,
        'symbol': symbol,
        'side': side,  # LONG or SHORT
        'quantity': quantity,
        'entry_price': entry_price,
        'current_price': entry_price,
        'status': 'OPEN',
        'unrealized_pnl': 0.0,
        'realized_pnl': 0.0
    })

    # Subscribe to price updates for this symbol
    await subscribe_to_price_feed(symbol, position.id)

    return position

async def update_position_price(position_id, current_price):
    """Update position with latest price"""

    position = await position_repository.get(position_id)

    # Calculate unrealized P&L
    if position.side == 'LONG':
        pnl = (current_price - position.entry_price) * position.quantity
    else:  # SHORT
        pnl = (position.entry_price - current_price) * position.quantity

    # Update position
    await position_repository.update(position_id, {
        'current_price': current_price,
        'unrealized_pnl': pnl
    })

    # Check stop-loss and take-profit
    if position.stop_loss and current_price <= position.stop_loss:
        await close_position(position_id, reason='STOP_LOSS')

    if position.take_profit and current_price >= position.take_profit:
        await close_position(position_id, reason='TAKE_PROFIT')
```

---

### **Step 4: Technical Analysis & Pattern Detection**

```
┌──────────────┐         ┌──────────────────┐         ┌──────────────┐
│ Market Data  │ ───────→│ Technical        │ ───────→│  RabbitMQ    │
│  (New Tick)  │  Event  │ Analyst Service  │ Signal  │ (Signals)    │
└──────────────┘         └──────────────────┘         └──────────────┘
                                   │
                                   ↓
                         ┌──────────────────┐
                         │  Pattern Engine  │
                         │                  │
                         │  • SMC Patterns  │
                         │  • Elliott Wave  │
                         │  • Indicators    │
                         │  • ML Models     │
                         └──────────────────┘
```

**Technical Analyst Service:**

1. **Pattern Detection Algorithms** (21 total)
   - **SMC (Smart Money Concepts):** 13 patterns
     - Order Blocks (Bullish/Bearish)
     - Fair Value Gaps (FVG)
     - Liquidity Voids
     - Break of Structure (BOS)
     - Change of Character (CHoCH)
     - Equal Highs/Lows
     - Imbalances

   - **Elliott Wave Theory:** 8 patterns
     - Impulse Waves (1-2-3-4-5)
     - Corrective Waves (A-B-C)
     - Extensions
     - Triangles

2. **Technical Indicators**
   ```python
   # Calculate indicators using TA-Lib
   indicators = {
       'rsi': talib.RSI(close_prices, timeperiod=14),
       'macd': talib.MACD(close_prices),
       'bollinger': talib.BBANDS(close_prices),
       'ema_9': talib.EMA(close_prices, 9),
       'ema_21': talib.EMA(close_prices, 21),
       'ema_50': talib.EMA(close_prices, 50)
   }
   ```

3. **Signal Generation**
   ```python
   async def analyze_and_generate_signals(symbol, timeframe):
       # 1. Get recent candles
       candles = await get_candles(symbol, timeframe, limit=200)

       # 2. Detect patterns
       patterns = await pattern_detector.detect_all(candles)

       # 3. Calculate indicators
       indicators = await calculate_indicators(candles)

       # 4. Generate signal
       if pattern_detector.has_bullish_pattern(patterns):
           if indicators['rsi'] < 30:  # Oversold
               signal = {
                   'symbol': symbol,
                   'direction': 'BUY',
                   'confidence': calculate_confidence(patterns, indicators),
                   'entry_price': candles[-1].close,
                   'stop_loss': calculate_stop_loss(patterns),
                   'take_profit': calculate_take_profit(patterns)
               }

               await publish_signal(signal)
   ```

---

## 📊 **Database Schema & Data Models**

### **TimescaleDB Hypertables** (Optimized for Time-Series)

```sql
-- Market Data Ticks
CREATE TABLE market_ticks (
    time TIMESTAMPTZ NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    volume DECIMAL(20, 8),
    exchange VARCHAR(50),
    PRIMARY KEY (time, symbol)
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('market_ticks', 'time');

-- Create continuous aggregate for 1-minute OHLCV
CREATE MATERIALIZED VIEW market_ohlcv_1m
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    FIRST(price, time) AS open,
    MAX(price) AS high,
    MIN(price) AS low,
    LAST(price, time) AS close,
    SUM(volume) AS volume
FROM market_ticks
GROUP BY bucket, symbol;

-- Retention policy: Keep ticks for 30 days
SELECT add_retention_policy('market_ticks', INTERVAL '30 days');
```

### **PostgreSQL Tables**

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    is_superuser BOOLEAN DEFAULT false,
    initial_capital DECIMAL(20, 2),
    current_capital DECIMAL(20, 2),
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- BUY, SELL
    type VARCHAR(20) NOT NULL,  -- MARKET, LIMIT, STOP
    quantity DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL,  -- PENDING, FILLED, CANCELLED
    filled_quantity DECIMAL(20, 8) DEFAULT 0,
    average_fill_price DECIMAL(20, 8),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    filled_at TIMESTAMPTZ
);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- LONG, SHORT
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    stop_loss DECIMAL(20, 8),
    take_profit DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    realized_pnl DECIMAL(20, 8),
    status VARCHAR(20) NOT NULL,  -- OPEN, CLOSED
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    closed_at TIMESTAMPTZ
);
```

---

## 🔐 **Security Architecture**

### **Authentication Flow**

```
┌────────────┐           ┌────────────┐           ┌────────────┐
│  Frontend  │           │  Gateway   │           │    Auth    │
│            │           │            │           │  Service   │
│            │ ─── 1 ───→│            │ ─── 2 ───→│            │
│            │           │            │           │  JWT Sign  │
│            │ ←── 4 ──  │  Validate  │ ← ── 3 ── │            │
│            │   Token   │    JWT     │   Token   │            │
└────────────┘           └────────────┘           └────────────┘

1. User login (email + password)
2. Verify credentials, generate JWT
3. Return signed JWT (access + refresh)
4. Store JWT in httpOnly cookie / localStorage
```

**JWT Token Structure:**
```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "email": "trader@example.com",
  "username": "trader1",
  "is_active": true,
  "is_superuser": false,
  "exp": 1640000000,
  "iat": 1639998200,
  "type": "access"
}
```

**Authorization:**
- All protected endpoints require `Authorization: Bearer <token>` header
- Gateway validates JWT before forwarding to services
- Gateway extracts user context and passes via `X-User-ID` header to services
- Services trust gateway-provided user context

---

## 📡 **Event-Driven Architecture**

### **Redis Pub/Sub Channels**

```python
# Market data events
CHANNELS = {
    'market.{symbol}.tick': 'Real-time tick data',
    'market.{symbol}.trade': 'Trade executions',
    'market.{symbol}.ohlcv.{timeframe}': 'OHLCV bars',

    'order.created': 'New order created',
    'order.filled': 'Order filled',
    'order.cancelled': 'Order cancelled',

    'position.opened': 'New position opened',
    'position.updated': 'Position updated',
    'position.closed': 'Position closed',

    'signal.generated': 'Trading signal generated',
    'alert.price': 'Price alert triggered'
}
```

### **RabbitMQ Message Queues**

```
┌─────────────────────────────────────────────────────────────┐
│                    RabbitMQ Exchanges                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  orders_exchange (topic)                                     │
│  ├─ orders.new → Order Executor Queue                        │
│  ├─ orders.filled → Position Manager Queue                   │
│  └─ orders.cancelled → Notification Queue                    │
│                                                              │
│  market_data_exchange (fanout)                               │
│  ├─ Technical Analyst Queue                                  │
│  ├─ Risk Manager Queue                                       │
│  └─ Analytics Queue                                          │
│                                                              │
│  signals_exchange (topic)                                    │
│  ├─ signals.high_confidence → Auto Trader Queue              │
│  └─ signals.* → Notification Queue                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 **Monitoring & Observability**

### **Prometheus Metrics**

```python
# Service-level metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'endpoint', 'method', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['service', 'endpoint', 'method']
)

# Business metrics
orders_created_total = Counter(
    'orders_created_total',
    'Total orders created',
    ['user_id', 'symbol', 'side']
)

positions_pnl = Gauge(
    'positions_unrealized_pnl',
    'Unrealized P&L of open positions',
    ['user_id', 'symbol']
)

market_data_ticks_processed = Counter(
    'market_data_ticks_processed',
    'Market data ticks processed',
    ['source', 'symbol']
)
```

### **Grafana Dashboards**

1. **System Health Dashboard**
   - Service uptime %
   - Request rate (req/s)
   - Error rate %
   - Response time (p50, p95, p99)

2. **Trading Dashboard**
   - Active positions
   - Total P&L
   - Win rate %
   - Average trade duration

3. **Market Data Dashboard**
   - Ticks processed/second
   - WebSocket connection status
   - Data latency
   - Symbol coverage

---

## 🚀 **Deployment Architecture**

### **Docker Compose Services**

```yaml
Current Deployment (Ports):
├─ PostgreSQL (TimescaleDB): 5432  [HEALTHY]
├─ Redis: 6379                      [HEALTHY]
├─ RabbitMQ: 5672, 15672           [HEALTHY]
├─ Prometheus: 9090                 [RUNNING]
├─ Grafana: 3001                    [RUNNING]
├─ Gateway: 8080                    [OPERATIONAL]
├─ Auth Service: 8001               [OPERATIONAL]
├─ Trading Service: 8002            [OPERATIONAL]
├─ Market Data Service: 8003        [HEALTHY]
└─ Frontend: 3000                   [NATIVE]
```

### **Service Communication**

```
Internal Network (Docker):
- Services communicate via service names (e.g., http://auth-service:8000)
- PostgreSQL: postgresql://testuser:testpass@postgres:5432/terminal_db
- Redis: redis://redis:6379/0
- RabbitMQ: amqp://trading:changeme@rabbitmq:5672/

External Access (Host):
- All services exposed via localhost:PORT
- Frontend proxies API requests to Gateway (localhost:8080)
```

---

## 🔄 **Complete Request Lifecycle Example**

### **User Registers → Receives Signal → Places Trade → Position Managed**

```
1. USER REGISTRATION
   Frontend → Gateway → Auth Service → PostgreSQL
   ✓ Password hashed with bcrypt
   ✓ User record created
   ✓ JWT tokens generated
   ✓ Tokens returned to frontend

2. MARKET DATA SUBSCRIPTION
   Market Data Service connects to:
   ├─ Alpaca WebSocket (stocks)
   └─ Binance WebSocket (crypto)

   For each tick:
   ├─ Store in TimescaleDB
   ├─ Publish to Redis (real-time)
   └─ Broadcast to WebSocket clients

3. SIGNAL GENERATION
   Technical Analyst Service:
   ├─ Subscribes to market data events
   ├─ Analyzes patterns + indicators
   ├─ Generates trading signal
   └─ Publishes to RabbitMQ

4. USER PLACES TRADE
   Frontend → Gateway (JWT auth) → Trading Service
   ├─ Validate order parameters
   ├─ Check user capital
   ├─ Create order in PostgreSQL
   ├─ Publish to order execution queue
   └─ Return order confirmation

5. ORDER EXECUTION
   Order Executor:
   ├─ Picks order from queue
   ├─ Sends to broker API
   ├─ Receives fill confirmation
   ├─ Updates order status
   └─ Creates position

6. POSITION MANAGEMENT
   Position Manager:
   ├─ Subscribes to price updates
   ├─ Calculates real-time P&L
   ├─ Checks stop-loss/take-profit
   ├─ Publishes position updates
   └─ Closes position when triggered

7. PORTFOLIO UPDATE
   Trading Service:
   ├─ Aggregates all positions
   ├─ Calculates total P&L
   ├─ Updates user capital
   └─ Broadcasts to frontend

8. REAL-TIME DASHBOARD
   Frontend:
   ├─ Receives WebSocket updates
   ├─ Updates charts in real-time
   ├─ Shows current positions
   └─ Displays P&L
```

---

## 🎯 **Key System Features**

### ✅ **Implemented & Operational**

1. **Multi-Asset Support**
   - Stocks (via Alpaca)
   - Crypto (via Binance)
   - Ready for Forex (OANDA integration available)

2. **Real-Time Data Processing**
   - WebSocket connections to exchanges
   - Sub-second latency
   - Automatic reconnection
   - Data normalization

3. **Pattern Detection** (21 Algorithms)
   - Smart Money Concepts (13 patterns)
   - Elliott Wave Theory (8 patterns)
   - Technical indicators (RSI, MACD, Bollinger, EMAs)

4. **Order Management**
   - Market, Limit, Stop orders
   - Position tracking
   - P&L calculation
   - Stop-loss & Take-profit

5. **Security**
   - JWT authentication
   - Bcrypt password hashing
   - API rate limiting
   - Role-based access control

6. **Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Health checks
   - Structured logging

---

## 📝 **API Endpoints Reference**

### **Auth Service (Port 8001)**
```
POST   /auth/register       Register new user
POST   /auth/login          Login & get JWT tokens
POST   /auth/refresh        Refresh access token
GET    /auth/me             Get current user
GET    /auth/health         Health check
```

### **Trading Service (Port 8002)**
```
POST   /orders              Create new order
GET    /orders              Get user orders
GET    /orders/{id}         Get order details
DELETE /orders/{id}         Cancel order

GET    /positions           Get user positions
GET    /positions/{id}      Get position details
POST   /positions/{id}/close Close position

GET    /portfolio           Get portfolio summary
GET    /health              Health check
```

### **Market Data Service (Port 8003)**
```
GET    /api/v1/symbols      Get available symbols
GET    /api/v1/quote/{symbol}        Get latest quote
GET    /api/v1/candles/{symbol}      Get OHLCV candles
GET    /api/v1/status       Get service status
GET    /api/v1/health       Health check
WS     /ws                  WebSocket connection
```

---

## 🎓 **System Design Principles**

1. **Microservices Architecture**
   - Each service has single responsibility
   - Services are independently deployable
   - Loose coupling via events

2. **Event-Driven Design**
   - Services communicate via events
   - Asynchronous processing
   - Scalable and resilient

3. **Domain-Driven Design**
   - Clear bounded contexts
   - Rich domain models
   - Repository pattern

4. **CQRS Pattern** (where applicable)
   - Separate read/write models
   - Optimized queries
   - Event sourcing ready

5. **Clean Architecture**
   - Transport layer (FastAPI)
   - Business logic (Services)
   - Data access (Repositories)
   - Domain models

---

## 🚧 **Future Enhancements**

1. **Machine Learning Integration**
   - Price prediction models
   - Sentiment analysis
   - Risk scoring

2. **Advanced Order Types**
   - OCO (One-Cancels-Other)
   - Trailing stop-loss
   - Iceberg orders

3. **Backtesting Engine**
   - Historical strategy testing
   - Performance analytics
   - Optimization

4. **Social Trading**
   - Copy trading
   - Strategy sharing
   - Leaderboard

---

**This architecture provides a production-ready, scalable foundation for AI-powered trading across multiple asset classes.**
