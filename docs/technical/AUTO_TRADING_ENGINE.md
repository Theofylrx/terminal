# Auto-Trading Engine - Technical Documentation

**Service**: Auto-Trading Engine
**Version**: 0.1.0
**Port**: 8005
**Container**: terminal-auto-trading
**Status**: ✅ Production Ready

---

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Decision Logic](#decision-logic)
5. [API Reference](#api-reference)
6. [Database Schema](#database-schema)
7. [Configuration](#configuration)
8. [Deployment](#deployment)
9. [Monitoring](#monitoring)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The **Auto-Trading Engine** is an autonomous trading orchestration service that enables 24/7 algorithmic trading for Terminal users. It continuously monitors markets, evaluates trading opportunities, and executes trades without human intervention.

### Key Capabilities
- **Autonomous Entry**: Scans enabled symbols for high-confidence entry signals
- **Intelligent Exits**: 5 exit scenarios covering profit protection, stop-loss, and trend following
- **Risk Management**: Position sizing, daily loss limits, concurrent position limits
- **Confluence Analysis**: Combines technical + fundamental analysis for higher quality decisions
- **Full Automation**: Operates 24/7 even when user is offline

### Design Philosophy
- **Orchestrator, Not Duplicator**: Calls existing agents (Technical Analyst, Market Data, Executor) rather than reimplementing logic
- **Safety First**: Multiple circuit breakers and emergency shutdown mechanisms
- **Audit Everything**: Complete decision trail for compliance and debugging
- **Fail Gracefully**: Service continues operating even if individual trades fail

---

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Auto-Trading Engine                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌───────────────┐  ┌────────────────────┐  │
│  │   Symbol     │  │   Position    │  │     Session        │  │
│  │   Monitor    │  │   Monitor     │  │     Manager        │  │
│  │   (5s)       │  │   (5s)        │  │     (60s)          │  │
│  └──────┬───────┘  └───────┬───────┘  └─────────┬──────────┘  │
│         │                  │                     │             │
│         └──────────┬───────┴─────────────────────┘             │
│                    │                                           │
│         ┌──────────▼──────────────┐                           │
│         │   Decision Engine       │                           │
│         │  (Entry/Exit Logic)     │                           │
│         └──────────┬──────────────┘                           │
│                    │                                           │
│         ┌──────────▼──────────────┐                           │
│         │  Service Integration    │                           │
│         │  (HTTP Clients)         │                           │
│         └──────────┬──────────────┘                           │
└────────────────────┼───────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
┌─────▼─────┐  ┌────▼─────┐  ┌────▼────────┐
│  Market   │  │Technical │  │  Executor   │
│   Data    │  │ Analyst  │  │   Service   │
└───────────┘  └──────────┘  └─────────────┘
```

### Technology Stack
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL (async via AsyncPG)
- **ORM**: SQLAlchemy 2.0 (async mode)
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic
- **Containerization**: Docker (multi-stage build)
- **Monitoring**: Prometheus metrics

---

## Components

### 1. Background Workers

#### Symbol Monitor Worker
**Purpose**: Scans enabled symbols for entry opportunities
**Interval**: 5 seconds
**Flow**:
1. Get all enabled auto-trading configurations
2. For each enabled symbol:
   - Fetch latest quote from Market Data Service
   - Request technical analysis from Technical Analyst Service
   - Evaluate entry signal using Decision Engine
   - If signal strength >= threshold:
     - Calculate position size via Executor Service
     - Execute trade via Executor Service
     - Send notification to user
     - Update session statistics

**Metrics Tracked**:
- `symbols_monitored`: Total symbols scanned
- `signals_detected`: Entry signals identified
- `trades_executed`: Trades successfully placed
- `trades_rejected`: Signals below confidence threshold

#### Position Monitor Worker
**Purpose**: Monitors open positions for exit opportunities
**Interval**: 5 seconds
**Flow**:
1. Get all open auto-traded positions from Trading Service
2. For each position:
   - Fetch current market price
   - Calculate current P&L
   - Request latest technical analysis
   - Evaluate exit signal using Decision Engine
   - Execute action (CLOSE, ADJUST_STOP, or HOLD)
   - Send notification if position closed
   - Update session statistics

**Metrics Tracked**:
- `positions_monitored`: Total positions checked
- `positions_closed`: Positions exited
- `stops_adjusted`: Trailing stop adjustments
- `profit_protections`: Exits for profit protection
- `stop_losses`: Stop-loss exits

#### Session Manager Worker
**Purpose**: Housekeeping and emergency shutdown
**Interval**: 60 seconds
**Flow**:
1. Check if new trading day (reset daily loss counters)
2. For each active session:
   - Check account drawdown vs emergency threshold
   - Check daily loss vs configured limit
   - Update session activity timestamp
   - Clean up stale sessions
3. Trigger emergency shutdown if needed

**Metrics Tracked**:
- `sessions_managed`: Sessions processed
- `daily_resets`: Daily counter resets
- `emergency_shutdowns`: Emergency stops triggered
- `configs_paused`: Configs auto-paused

### 2. Decision Engine

**Purpose**: AI brain for autonomous trading decisions
**Location**: `/services/auto-trading-engine/services/decision_engine.py`

#### Entry Decision Logic

```python
async def evaluate_entry_signal(
    symbol, technical_analysis, fundamental_analysis, config, current_price
):
    # 1. Fundamental Filter (Tier 1)
    if fundamental_analysis and config.use_fundamental_filter:
        if not passes_fundamental_filter(fundamental_analysis):
            return Decision(action=HOLD, reason="Fundamental filter failed")

    # 2. Technical Confidence Check
    technical_confidence = technical_analysis['confidence']
    if technical_confidence < config.entry_confidence_threshold:
        return Decision(action=HOLD, reason="Low confidence")

    # 3. Confluence Boost (Tier 2)
    fundamental_boost = calculate_confluence_boost(
        fundamental_analysis, technical_analysis
    )
    final_confidence = technical_confidence + fundamental_boost

    # 4. Risk Adjustment (Tier 3)
    risk_multiplier = calculate_risk_multiplier(fundamental_analysis)

    # 5. Entry Decision
    return Decision(
        action=ENTER,
        side=technical_analysis['direction'],
        confidence=final_confidence,
        risk_multiplier=risk_multiplier
    )
```

#### Exit Decision Logic (5 Scenarios)

```python
async def evaluate_exit_signal(
    position, current_price, pnl_data, technical_analysis, config
):
    pnl_percent = pnl_data['pnl_percent']
    correction_probability = technical_analysis.get('correction_probability', 0)
    reversal_probability = technical_analysis.get('reversal_probability', 0)

    # SCENARIO 1: In Profit + Correction Detected → CLOSE
    if pnl_percent > 0 and correction_probability > 70:
        return Decision(
            action=CLOSE,
            reason='PROFIT_PROTECTION',
            confidence=correction_probability
        )

    # SCENARIO 2: In Profit + Trend Continues → ADJUST TRAILING STOP
    if pnl_percent > 0 and trend_aligns_with_position:
        new_stop = calculate_trailing_stop(current_price, position, config)
        return Decision(
            action=ADJUST_STOP,
            new_stop_loss=new_stop,
            reason='TRAILING_STOP'
        )

    # SCENARIO 3: In Loss + Reversal Likely → HOLD
    if pnl_percent < 0 and reversal_probability > 60:
        return Decision(
            action=HOLD,
            reason='POTENTIAL_REVERSAL',
            confidence=reversal_probability
        )

    # SCENARIO 4: In Loss + No Recovery → CUT LOSS
    if pnl_percent < 0 and not reversal_likely:
        return Decision(
            action=CLOSE,
            reason='STOP_LOSS_NO_RECOVERY',
            confidence=80 + abs(pnl_percent) * 2
        )

    # SCENARIO 5: Strong Opposite Trend → EXIT
    if not trend_aligns_with_position:
        return Decision(
            action=CLOSE,
            reason='TREND_REVERSAL',
            confidence=technical_analysis['confidence']
        )

    # Default: HOLD
    return Decision(action=HOLD, reason='NO_EXIT_SIGNAL')
```

#### 3-Tier Confluence System

**Tier 1: Fundamental Filtering**
- Optional pre-filter for symbol selection
- Excludes symbols with poor fundamentals
- Example: P/E ratio, debt levels, earnings growth

**Tier 2: Confidence Boosting**
- Enhances technical signal strength
- Fundamental + Technical alignment = higher confidence
- Example: Strong technical + strong fundamentals = +10-15% confidence

**Tier 3: Risk Adjustment**
- Modifies position sizing based on fundamentals
- Strong fundamentals = larger position size
- Weak fundamentals = smaller position size

### 3. Service Integration Clients

All clients extend `HTTPClient` base class with centralized error handling.

#### Market Data Client
```python
async def get_latest_quote(symbol: str) -> Dict:
    """Get current price, bid, ask, volume"""

async def get_historical_data(symbol: str, timeframe: str, bars: int) -> List[Dict]:
    """Get OHLCV historical data"""
```

#### Technical Analyst Client
```python
async def analyze(
    symbol: str,
    timeframes: List[str],
    include_reasoning: bool = True
) -> Dict:
    """Get technical analysis with patterns, indicators, signals"""
```

#### Executor Client
```python
async def calculate_position_size(
    user_id: str,
    symbol: str,
    entry_price: Decimal,
    risk_percent: float,
    stop_loss_percent: float
) -> Dict:
    """Calculate optimal position size based on risk"""

async def execute_market_order(
    user_id: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    stop_loss: Decimal,
    take_profit: Optional[Decimal],
    metadata: Dict
) -> Dict:
    """Execute market order with stop-loss"""

async def close_position(
    position_id: str,
    reason: str,
    confidence: float
) -> Dict:
    """Close open position"""
```

#### Trading Client
```python
async def get_open_positions(
    user_id: Optional[str] = None,
    auto_trade_only: bool = False
) -> List[Dict]:
    """Get open positions"""

async def calculate_pnl(
    position_id: str,
    current_price: Decimal
) -> Dict:
    """Calculate current P&L for position"""
```

#### Notification Client
```python
async def send_trade_entry_notification(
    user_id: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    entry_price: Decimal,
    confidence: float
):
    """Notify user of trade entry"""

async def send_trade_exit_notification(
    user_id: str,
    symbol: str,
    pnl: Decimal,
    pnl_percent: float,
    reason: str
):
    """Notify user of trade exit"""
```

---

## API Reference

### Configuration Endpoints

**Base URL**: `http://localhost:8005/api/v1/config`

#### Create Configuration
```http
POST /api/v1/config?user_id={user_id}
Content-Type: application/json

{
  "symbol": "AAPL",
  "broker": "alpaca",
  "asset_class": "stocks",
  "risk_per_trade_percent": 1.0,
  "max_concurrent_positions": 3,
  "max_daily_loss_percent": 5.0,
  "stop_loss_percent": 2.0,
  "strategy_type": "BALANCED",
  "entry_confidence_threshold": 70.0,
  "trading_start_hour": 0,
  "trading_end_hour": 23,
  "auto_close_on_correction": true,
  "trailing_stop_enabled": true,
  "trailing_stop_percent": 2.0
}
```

#### Get All Configurations
```http
GET /api/v1/config?user_id={user_id}
```

#### Get Configuration by ID
```http
GET /api/v1/config/{config_id}
```

#### Update Configuration
```http
PATCH /api/v1/config/{config_id}
Content-Type: application/json

{
  "entry_confidence_threshold": 75.0,
  "stop_loss_percent": 2.5
}
```

#### Enable Auto-Trading
```http
POST /api/v1/config/{config_id}/enable
```
- Sets `enabled = true`
- Creates new auto-trading session

#### Disable Auto-Trading
```http
POST /api/v1/config/{config_id}/disable
```
- Sets `enabled = false`
- Stops active session

#### Delete Configuration
```http
DELETE /api/v1/config/{config_id}
```

#### Get Session Statistics
```http
GET /api/v1/config/{config_id}/session
```

Response:
```json
{
  "id": "session-uuid",
  "symbol": "AAPL",
  "status": "ACTIVE",
  "total_trades": 15,
  "winning_trades": 10,
  "losing_trades": 5,
  "win_rate": 66.67,
  "total_pnl": 1250.50,
  "best_trade_pnl": 350.00,
  "worst_trade_pnl": -125.00,
  "current_open_positions": 1,
  "daily_loss": -50.00,
  "started_at": "2024-01-20T10:00:00Z",
  "last_activity_at": "2024-01-20T14:30:00Z"
}
```

### System Endpoints

#### Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "auto-trading-engine",
  "version": "0.1.0",
  "workers": {
    "symbol_monitor": true,
    "position_monitor": true,
    "session_manager": true
  }
}
```

#### Worker Status
```http
GET /workers/status
```

Response: Detailed worker statistics including iterations, errors, and custom metrics

---

## Database Schema

### auto_trading_configs
**Purpose**: User configurations for auto-trading on specific symbols

```sql
CREATE TABLE auto_trading_configs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT false NOT NULL,

    -- Risk Parameters
    risk_per_trade_percent DECIMAL(5,2) DEFAULT 1.0 NOT NULL,
    max_concurrent_positions INTEGER DEFAULT 3 NOT NULL,
    max_daily_loss_percent DECIMAL(5,2) DEFAULT 5.0 NOT NULL,
    stop_loss_percent DECIMAL(5,2) DEFAULT 2.0 NOT NULL,

    -- Strategy Settings
    strategy_type strategy_type DEFAULT 'BALANCED' NOT NULL,
    entry_confidence_threshold DECIMAL(5,2) DEFAULT 70.0 NOT NULL,

    -- Trading Hours (UTC)
    trading_start_hour INTEGER DEFAULT 0 NOT NULL,
    trading_end_hour INTEGER DEFAULT 23 NOT NULL,

    -- Auto-Management Settings
    auto_close_on_correction BOOLEAN DEFAULT true NOT NULL,
    trailing_stop_enabled BOOLEAN DEFAULT true NOT NULL,
    trailing_stop_percent DECIMAL(5,2) DEFAULT 2.0 NOT NULL,

    -- Metadata
    broker VARCHAR(50) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT unique_user_symbol UNIQUE(user_id, symbol)
);
```

**Indexes**: user_id, symbol, enabled, (user_id, enabled)

### auto_trading_sessions
**Purpose**: Active and historical auto-trading sessions with statistics

```sql
CREATE TABLE auto_trading_sessions (
    id VARCHAR(36) PRIMARY KEY,
    config_id VARCHAR(36) NOT NULL REFERENCES auto_trading_configs(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    status session_status DEFAULT 'ACTIVE' NOT NULL,

    -- Session Statistics
    total_trades INTEGER DEFAULT 0 NOT NULL,
    winning_trades INTEGER DEFAULT 0 NOT NULL,
    losing_trades INTEGER DEFAULT 0 NOT NULL,
    total_pnl DECIMAL(20,8) DEFAULT 0 NOT NULL,
    best_trade_pnl DECIMAL(20,8) DEFAULT 0 NOT NULL,
    worst_trade_pnl DECIMAL(20,8) DEFAULT 0 NOT NULL,

    -- Risk Tracking
    current_open_positions INTEGER DEFAULT 0 NOT NULL,
    daily_loss DECIMAL(20,8) DEFAULT 0 NOT NULL,
    last_trade_at TIMESTAMPTZ,

    -- Session Timing
    started_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    last_activity_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,

    -- Error Tracking
    error_count INTEGER DEFAULT 0 NOT NULL,
    last_error_message VARCHAR(500),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

**Indexes**: config_id, user_id, symbol, status, (user_id, status), (status, last_activity_at) WHERE status = 'ACTIVE'

### position_decisions
**Purpose**: Audit trail of AI decisions for position management

```sql
CREATE TABLE position_decisions (
    id VARCHAR(36) PRIMARY KEY,
    position_id VARCHAR(36) NOT NULL REFERENCES positions(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Market State
    current_price DECIMAL(20,8) NOT NULL,
    pnl_percent DECIMAL(10,4) NOT NULL,

    -- Signals
    trend_direction VARCHAR(20),
    correction_probability DECIMAL(5,2),
    reversal_probability DECIMAL(5,2),

    -- Decision
    action VARCHAR(20) NOT NULL CHECK (action IN ('HOLD', 'CLOSE', 'ADJUST_STOP')),
    reason TEXT NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,

    -- Execution
    executed BOOLEAN DEFAULT false NOT NULL,
    execution_price DECIMAL(20,8),
    execution_time TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);
```

**Indexes**: position_id, timestamp DESC, action, executed

### ENUM Types

```sql
CREATE TYPE strategy_type AS ENUM ('AGGRESSIVE', 'BALANCED', 'CONSERVATIVE');
CREATE TYPE session_status AS ENUM ('ACTIVE', 'PAUSED', 'STOPPED', 'ERROR');
```

---

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/terminal_db

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://trading:changeme@rabbitmq:5672/

# Service URLs
MARKET_DATA_SERVICE_URL=http://market-data-service:8000
TECHNICAL_ANALYST_SERVICE_URL=http://technical-analyst-service:8000
EXECUTOR_SERVICE_URL=http://executor-service:8000
TRADING_SERVICE_URL=http://trading-service:8000
NOTIFICATION_SERVICE_URL=http://notification-service:8000

# Application
ENVIRONMENT=development|staging|production
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR
DEBUG=true|false

# Worker Intervals (seconds)
SYMBOL_MONITOR_INTERVAL_SECONDS=5
POSITION_MONITOR_INTERVAL_SECONDS=5
SESSION_MANAGER_INTERVAL_SECONDS=60

# Monitoring
ENABLE_PROMETHEUS_METRICS=true
```

### Configuration Constraints

- `risk_per_trade_percent`: 0.1% - 5.0%
- `max_concurrent_positions`: 1 - 10
- `max_daily_loss_percent`: 1.0% - 15.0%
- `stop_loss_percent`: 0.5% - 10.0%
- `entry_confidence_threshold`: 50.0% - 95.0%
- `trailing_stop_percent`: 0.5% - 5.0%

---

## Deployment

### Docker Build
```bash
docker-compose build auto-trading-engine
```

### Start Service
```bash
docker-compose up -d auto-trading-engine
```

### Check Logs
```bash
docker logs -f terminal-auto-trading
```

### Check Health
```bash
curl http://localhost:8005/health
```

### Restart Service
```bash
docker-compose restart auto-trading-engine
```

---

## Monitoring

### Prometheus Metrics
The service exposes Prometheus metrics at `/metrics`:

- Request duration
- Request count by endpoint
- HTTP status codes
- Worker iteration counts
- Worker error counts

### Worker Statistics
Access detailed worker stats via `/workers/status`:

```json
{
  "symbol_monitor": {
    "running": true,
    "iterations": 1000,
    "errors": 0,
    "symbols_monitored": 150,
    "signals_detected": 12,
    "trades_executed": 8
  }
}
```

### Health Checks

**Container Health Check**:
```bash
curl -f http://localhost:8005/health || exit 1
```

**Worker Health**:
All workers must be `running: true` with `errors: 0`

---

## Troubleshooting

### Workers Not Starting

**Symptom**: Workers show as stopped in `/health` endpoint

**Causes**:
1. Database connection failure
2. Missing environment variables
3. Service integration failures

**Solution**:
```bash
# Check logs
docker logs terminal-auto-trading | grep ERROR

# Verify database connectivity
docker exec terminal-auto-trading python -c "from shared.database.connection import init_db; init_db()"

# Check environment variables
docker exec terminal-auto-trading env | grep SERVICE_URL
```

### High Error Rate

**Symptom**: Worker stats show `errors > 0`

**Causes**:
1. Dependent service unavailable (404 errors are expected if services not implemented)
2. Database ENUM type mismatch
3. Network issues

**Solution**:
```bash
# Check which worker has errors
curl http://localhost:8005/workers/status | jq '.[] | select(.stats.errors > 0)'

# Review logs for specific error
docker logs terminal-auto-trading | grep "❌"
```

### Database ENUM Errors

**Symptom**: `type "session_status" does not exist`

**Solution**:
```bash
# Run ENUM migration
docker exec -i terminal-postgres psql -U testuser -d terminal_db < shared/database/migrations/003_create_auto_trading_enums.sql
```

### Service Integration 404 Errors

**Symptom**: Logs show `HTTP error: 404 - /api/v1/positions`

**Cause**: Expected - dependent services haven't implemented endpoints yet

**Solution**: These errors are handled gracefully. Workers continue operating. Implement missing endpoints in dependent services.

---

## Security Considerations

1. **Non-Root User**: Container runs as `autotradinguser` (UID 1000)
2. **Read-Only Volumes**: Code mounted as read-only
3. **Environment Isolation**: Secrets via environment variables, not hardcoded
4. **Input Validation**: All API inputs validated via Pydantic
5. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
6. **Rate Limiting**: Should be added via API Gateway

---

## Performance Tuning

### Worker Intervals
- **High-frequency trading**: Reduce to 1-2 seconds
- **Long-term trading**: Increase to 30-60 seconds
- **Production**: 5s for Symbol/Position Monitor, 60s for Session Manager

### Database Connection Pool
```python
pool_size=10        # Concurrent connections
max_overflow=20     # Additional connections if pool exhausted
```

### HTTP Client Timeout
```python
timeout=30  # Seconds (default)
```

Adjust based on dependent service response times.

---

## Future Enhancements

1. **Fundamental Analyst Integration** - Add fundamental analysis client
2. **Multiple Strategies** - Support user-defined strategies beyond AGGRESSIVE/BALANCED/CONSERVATIVE
3. **Portfolio Rebalancing** - Automatic portfolio optimization
4. **Backtesting** - Historical strategy simulation
5. **Machine Learning** - Adaptive confidence thresholds
6. **WebSocket Subscriptions** - Real-time price feeds instead of polling
7. **Advanced Risk Management** - Portfolio-level risk limits
8. **Multi-Timeframe Analysis** - Combine multiple timeframes for confluence

---

**Last Updated**: 2024-01-20
**Maintained By**: Terminal AI Trading System Team
