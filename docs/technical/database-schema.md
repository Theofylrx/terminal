# Terminal Trading System - Complete Database Schema

**Date**: 2024-09-19
**Version**: 1.0.0
**Status**: Security Review - User Isolation Required

---

## 🚨 CRITICAL SECURITY REQUIREMENTS

**ALL user-specific data MUST include `user_id`** to prevent data leaks between users.

### ✅ **Correct Pattern**:
```python
user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
```

### ❌ **NEVER** store user-specific data without `user_id`!

---

## 📊 **DATABASE TABLES**

### **1. Core Tables** (Currently Implemented)

#### **`users`** - User Authentication & Profile
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_superuser BOOLEAN DEFAULT FALSE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    initial_capital FLOAT,
    current_capital FLOAT,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_email (email),
    INDEX idx_user_username (username)
);
```

**Relationships**:
- One user → Many positions
- One user → Many orders
- One user → Many signals
- One user → Many trading_decisions

---

#### **`positions`** - Trading Positions ✅ **HAS user_id**
```sql
CREATE TABLE positions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION
    symbol VARCHAR(20) NOT NULL,
    asset_class ENUM('STOCK', 'CRYPTO', 'FOREX', 'COMMODITY') NOT NULL,
    side ENUM('LONG', 'SHORT') NOT NULL,
    status ENUM('OPEN', 'CLOSED', 'LIQUIDATED') NOT NULL DEFAULT 'OPEN',
    quantity FLOAT NOT NULL,
    avg_entry_price FLOAT NOT NULL,
    current_price FLOAT,
    market_value FLOAT,
    cost_basis FLOAT NOT NULL,
    unrealized_pnl FLOAT DEFAULT 0.0,
    realized_pnl FLOAT DEFAULT 0.0,
    stop_loss_price FLOAT,
    take_profit_price FLOAT,
    broker VARCHAR(50),
    strategy_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_position_user_id (user_id),
    INDEX idx_position_symbol (symbol),
    INDEX idx_position_status (status)
);
```

---

#### **`orders`** - Trading Orders ✅ **HAS user_id**
```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION
    symbol VARCHAR(20) NOT NULL,
    asset_class ENUM('STOCK', 'CRYPTO', 'FOREX') NOT NULL,
    order_type ENUM('MARKET', 'LIMIT', 'STOP', 'STOP_LIMIT') NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    status ENUM('PENDING', 'FILLED', 'PARTIALLY_FILLED', 'CANCELLED', 'REJECTED') NOT NULL,
    quantity FLOAT NOT NULL,
    filled_quantity FLOAT DEFAULT 0.0,
    limit_price FLOAT,
    stop_price FLOAT,
    filled_price FLOAT,
    broker VARCHAR(50),
    broker_order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_order_user_id (user_id),
    INDEX idx_order_symbol (symbol),
    INDEX idx_order_status (status)
);
```

---

#### **`ohlcv`** - Market Data (NO user_id - shared market data)
```sql
CREATE TABLE ohlcv (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h', '4h', '1D', etc.
    timestamp TIMESTAMP NOT NULL,
    open FLOAT NOT NULL,
    high FLOAT NOT NULL,
    low FLOAT NOT NULL,
    close FLOAT NOT NULL,
    volume FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE INDEX idx_ohlcv_symbol_timeframe_timestamp (symbol, timeframe, timestamp),
    INDEX idx_ohlcv_symbol (symbol),
    INDEX idx_ohlcv_timestamp (timestamp)
);

-- Convert to TimescaleDB hypertable for performance
SELECT create_hypertable('ohlcv', 'timestamp');
```

**Note**: OHLCV data is SHARED (no user_id) - it's public market data.

---

### **2. Signal & Analysis Tables** (NEED user_id ADDED! 🚨)

#### **`signals`** - Trading Signals ❌ **MISSING user_id!**

**CURRENT (INSECURE)**:
```sql
-- ❌ CURRENT VERSION - NO USER ISOLATION
CREATE TABLE signals (
    id UUID PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal_type ENUM('buy', 'sell', 'hold') NOT NULL,
    status ENUM('active', 'executed', 'expired', 'cancelled') NOT NULL DEFAULT 'active',
    entry_price FLOAT NOT NULL,
    current_price FLOAT,
    target_price FLOAT,
    stop_loss FLOAT,
    confidence FLOAT NOT NULL,
    strategy VARCHAR(100),
    description TEXT,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**REQUIRED FIX** 🔧:
```sql
-- ✅ FIXED VERSION - WITH USER ISOLATION
CREATE TABLE signals (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ ADD THIS!
    symbol VARCHAR(20) NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    signal_type ENUM('buy', 'sell', 'hold') NOT NULL,
    status ENUM('active', 'executed', 'expired', 'cancelled') NOT NULL DEFAULT 'active',
    entry_price FLOAT NOT NULL,
    current_price FLOAT,
    target_price FLOAT,
    stop_loss FLOAT,
    confidence FLOAT NOT NULL,
    strategy VARCHAR(100),
    description TEXT,
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    executed_at TIMESTAMP,
    trading_decision_id UUID,  -- Link to TradingDecision
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- ✅ ADD THIS!
    FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE SET NULL,
    INDEX idx_signal_user_id (user_id),  -- ✅ ADD THIS!
    INDEX idx_signal_symbol_timeframe (symbol, timeframe),
    INDEX idx_signal_status (status),
    INDEX idx_signal_generated_at (generated_at)
);
```

---

#### **`trading_decisions`** - Complete Trading Decisions ❌ **MISSING user_id!**

**REQUIRED (WITH user_id)**:
```sql
CREATE TABLE trading_decisions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION REQUIRED
    symbol VARCHAR(20) NOT NULL,
    action ENUM('BUY', 'SELL', 'WAIT', 'CLOSE') NOT NULL,
    confidence FLOAT NOT NULL,  -- 0.0 to 1.0
    confidence_level ENUM('VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH') NOT NULL,
    should_trade VARCHAR(10) NOT NULL,  -- 'true' or 'false'

    -- Arguments (JSON)
    primary_arguments JSON NOT NULL,  -- [{"claim": "...", "evidence": [...], ...}]
    counter_arguments JSON NOT NULL,

    -- Fundamental alignment (JSON)
    fundamental_alignment JSON,  -- {"direction": "BULLISH", "strength": "STRONG", ...}

    -- Risk assessment (JSON)
    risk_assessment JSON NOT NULL,  -- {"risk_level": "LOW", "primary_risks": [...], ...}

    -- Entry plan (JSON)
    entry_plan JSON,  -- {"entry_price": 81250, "stop_loss": 81650, "targets": [...]}

    -- Timeframe summary (JSON)
    timeframe_summary JSON NOT NULL,  -- {"15M": {...}, "1H": {...}, ...}

    -- Confidence breakdown (JSON)
    confidence_breakdown JSON NOT NULL,  -- {"technical_confidence": 0.82, ...}

    -- Reasoning (TEXT - can be large)
    executive_summary TEXT NOT NULL,
    detailed_reasoning TEXT NOT NULL,

    -- Performance tracking (updated after trade)
    actual_entry_price FLOAT,
    actual_exit_price FLOAT,
    actual_pnl FLOAT,
    actual_pnl_percent FLOAT,
    trade_outcome VARCHAR(20),  -- 'WIN', 'LOSS', 'BREAKEVEN'

    -- Timestamps
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- ✅ REQUIRED!
    INDEX idx_trading_decision_user_id (user_id),  -- ✅ REQUIRED!
    INDEX idx_trading_decision_symbol (symbol),
    INDEX idx_trading_decision_action (action),
    INDEX idx_trading_decision_confidence (confidence),
    INDEX idx_trading_decision_generated_at (generated_at),
    INDEX idx_trading_decision_should_trade (should_trade)
);
```

---

#### **`evidence`** - Evidence Items ❌ **MISSING user_id!**

**REQUIRED (WITH user_id)**:
```sql
CREATE TABLE evidence (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION REQUIRED
    trading_decision_id UUID NOT NULL,
    source VARCHAR(100) NOT NULL,  -- "4H Timeframe", "Fundamental Analysis"
    type VARCHAR(100) NOT NULL,    -- "SMC Pattern", "Elliott Wave", "Indicator"
    description TEXT NOT NULL,
    score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    timestamp TIMESTAMP,
    metadata JSON,  -- Flexible storage for pattern-specific data
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- ✅ REQUIRED!
    FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE CASCADE,
    INDEX idx_evidence_user_id (user_id),  -- ✅ REQUIRED!
    INDEX idx_evidence_decision_id (trading_decision_id),
    INDEX idx_evidence_source (source),
    INDEX idx_evidence_type (type),
    INDEX idx_evidence_score (score)
);
```

---

#### **`analysis_reports`** - Complete Analysis Reports ❌ **MISSING user_id!**

**REQUIRED (WITH user_id)**:
```sql
CREATE TABLE analysis_reports (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION REQUIRED
    trading_decision_id UUID NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    report_type VARCHAR(50) NOT NULL,  -- 'MULTI_TIMEFRAME', 'SINGLE_TIMEFRAME'
    timeframes_analyzed JSON NOT NULL,  -- ["15M", "1H", "4H", "Daily"]
    analysis_data JSON NOT NULL,  -- Complete analysis data
    report_file_path VARCHAR(500),  -- Path if saved to disk
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,  -- ✅ REQUIRED!
    FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE CASCADE,
    INDEX idx_analysis_report_user_id (user_id),  -- ✅ REQUIRED!
    INDEX idx_analysis_report_decision_id (trading_decision_id),
    INDEX idx_analysis_report_symbol (symbol),
    INDEX idx_analysis_report_generated_at (generated_at)
);
```

---

### **3. Relationship Tables** (Future Implementation)

#### **`trades`** - Executed Trades ✅ **HAS user_id**
```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,  -- ✅ USER ISOLATION
    order_id UUID,
    symbol VARCHAR(20) NOT NULL,
    side ENUM('BUY', 'SELL') NOT NULL,
    quantity FLOAT NOT NULL,
    price FLOAT NOT NULL,
    commission FLOAT DEFAULT 0.0,
    pnl FLOAT,
    executed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL,
    INDEX idx_trade_user_id (user_id),
    INDEX idx_trade_symbol (symbol),
    INDEX idx_trade_executed_at (executed_at)
);
```

---

## 🔒 **SECURITY REQUIREMENTS**

### **1. Row-Level Security (RLS)**

Every query MUST filter by `user_id`:

```python
# ✅ CORRECT - User-isolated query
signals = session.query(Signal).filter(
    Signal.user_id == current_user.id,
    Signal.symbol == "BTCUSD"
).all()

# ❌ WRONG - Returns ALL users' signals!
signals = session.query(Signal).filter(
    Signal.symbol == "BTCUSD"
).all()
```

### **2. API Endpoint Protection**

Every endpoint MUST:
1. Authenticate the user
2. Filter by `user_id`
3. Never expose other users' data

```python
# Example: Protected endpoint
@router.get("/signals")
async def get_user_signals(
    current_user: User = Depends(get_current_user),  # ✅ Auth required
    session: AsyncSession = Depends(get_db_session)
):
    # ✅ Filter by current user
    signals = await session.execute(
        select(Signal).where(Signal.user_id == current_user.id)
    )
    return signals.scalars().all()
```

### **3. Database Constraints**

```sql
-- ✅ Ensure user_id is ALWAYS set
ALTER TABLE signals
    ALTER COLUMN user_id SET NOT NULL;

-- ✅ Cascade delete - when user deleted, delete their data
ALTER TABLE signals
    ADD CONSTRAINT fk_signal_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

---

## 📊 **DATABASE RELATIONSHIPS DIAGRAM**

```
┌─────────────┐
│    users    │
│  (id, ...)  │
└──────┬──────┘
       │
       ├───────────────────────────┐
       │                           │
       ▼                           ▼
┌──────────────┐          ┌──────────────────┐
│  positions   │          │     orders       │
│ (user_id,    │          │  (user_id, ...)  │
│   ...)       │          └──────────────────┘
└──────────────┘
       │
       ▼
┌─────────────────────┐
│ trading_decisions   │
│  (user_id, ...)     │
└──────┬──────────────┘
       │
       ├──────────┬─────────┐
       ▼          ▼         ▼
┌──────────┐ ┌──────────┐ ┌────────────────┐
│ signals  │ │ evidence │ │ analysis_      │
│(user_id) │ │(user_id) │ │ reports        │
│          │ │          │ │ (user_id)      │
└──────────┘ └──────────┘ └────────────────┘

┌──────────────┐
│    ohlcv     │  (NO user_id - shared market data)
│ (symbol,     │
│  timeframe,  │
│  timestamp)  │
└──────────────┘
```

---

## 🚨 **IMMEDIATE ACTION REQUIRED**

### **Critical Security Fixes**:

1. ✅ **Update Signal model** - Add `user_id`
2. ✅ **Update TradingDecision model** - Add `user_id`
3. ✅ **Update Evidence model** - Add `user_id`
4. ✅ **Update AnalysisReport model** - Add `user_id`
5. ✅ **Update all API endpoints** - Filter by `user_id`
6. ✅ **Create database migration** - Add user_id columns
7. ✅ **Add Row-Level Security policies**
8. ✅ **Update all queries** - Include user_id filter

---

## 📈 **QUERY PERFORMANCE**

### **Indexes Required**:

Every table with `user_id` MUST have:
```sql
CREATE INDEX idx_{table}_user_id ON {table}(user_id);
```

### **Composite Indexes**:
```sql
-- For common queries
CREATE INDEX idx_signal_user_symbol_timeframe
    ON signals(user_id, symbol, timeframe);

CREATE INDEX idx_trading_decision_user_symbol
    ON trading_decisions(user_id, symbol);

CREATE INDEX idx_evidence_user_decision
    ON evidence(user_id, trading_decision_id);
```

---

## 🔄 **DATA LIFECYCLE**

### **User Deletion**:
```sql
-- All user data should CASCADE delete
ON DELETE CASCADE
```

When a user is deleted:
1. ✅ All positions deleted
2. ✅ All orders deleted
3. ✅ All signals deleted
4. ✅ All trading_decisions deleted
5. ✅ All evidence deleted
6. ✅ All analysis_reports deleted

### **Data Retention**:
- Active signals: 7 days
- Expired signals: 30 days
- Trading decisions: 1 year
- Analysis reports: 1 year
- Completed trades: Indefinite (for performance tracking)

---

**Status**: 🚨 **CRITICAL SECURITY REVIEW REQUIRED**
**Priority**: **P0 - Must Fix Before Production**
**Estimated Impact**: 4 models, ~15 API endpoints, 1 migration
