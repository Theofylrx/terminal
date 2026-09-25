# Auto-Trading System - REVISED Architecture (Agent Orchestration)

**Feature:** Fully Autonomous AI Trading System
**Status:** Design Phase - REVISED
**Priority:** Critical

---

## 🎯 Key Architectural Principle

**The Auto-Trading Engine is an ORCHESTRATOR, not a duplicate.**

It leverages existing agents and services:
- ✅ **Market Data Service** - Real-time data feeds
- ✅ **Technical Analyst Service** - Pattern detection (21 algorithms)
- ✅ **Fundamental Analyst Service** - Fundamental analysis
- ✅ **Executor Service** - Order execution with risk management
- ✅ **Orchestrator Service** - Multi-agent coordination
- ✅ **Trading Service** - Position/order tracking
- ✅ **Notification Service** - User alerts

**Auto-Trading adds:**
- ❌ Symbol configuration & enable/disable UI
- ❌ 24/7 background monitoring workers
- ❌ Autonomous decision-making logic
- ❌ Session tracking & statistics
- ❌ Auto-trading specific risk parameters

---

## 🏗️ REVISED System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTO-TRADING ORCHESTRATION LAYER                     │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│  USER CONFIGURATION (Frontend)                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Auto-Trading Dashboard                                            │  │
│  │  • Enable/Disable symbols                                          │  │
│  │  • Set risk parameters (risk %, max positions, stop loss)          │  │
│  │  • Configure trading hours                                         │  │
│  │  • View session stats & AI decisions                               │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────┐
│  AUTO-TRADING ENGINE (NEW SERVICE)                                       │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Background Workers (24/7)                                         │  │
│  │  1. Symbol Monitor Worker                                          │  │
│  │     - Monitors enabled symbols                                     │  │
│  │     - Requests analysis from Technical Analyst                     │  │
│  │     - Evaluates entry signals                                      │  │
│  │                                                                     │  │
│  │  2. Position Monitor Worker                                        │  │
│  │     - Monitors all auto-traded positions                           │  │
│  │     - Requests market updates from Market Data                     │  │
│  │     - Requests analysis from Technical Analyst                     │  │
│  │     - Makes autonomous exit decisions                              │  │
│  │                                                                     │  │
│  │  3. Session Manager Worker                                         │  │
│  │     - Tracks session statistics                                    │  │
│  │     - Resets daily counters                                        │  │
│  │     - Handles emergency shutdowns                                  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
        ↓                    ↓                    ↓                    ↓
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Market     │    │  Technical   │    │   Executor   │    │  Trading     │
│   Data       │    │   Analyst    │    │   Service    │    │  Service     │
│   (Existing) │    │  (Existing)  │    │  (Existing)  │    │ (Existing)   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
│                    │                    │                    │
│ • WebSocket feeds  │ • 21 Patterns      │ • Order Manager   │ • Position DB
│ • Real-time quotes │ • SMC + Elliott    │ • Position Sizer  │ • Order DB
│ • Historical data  │ • Divergence       │ • Risk Manager    │ • P&L tracking
│                    │ • AI Reasoning     │ • Broker APIs     │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## 🔄 Complete Autonomous Trading Flow (Agent Integration)

### **Step 1: User Enables Symbol for Auto-Trading**

```
User Action (Frontend):
1. Navigate to Auto-Trading Dashboard
2. Select symbol (e.g., AAPL)
3. Configure parameters:
   - Risk per trade: 1%
   - Max positions: 3
   - Strategy: Balanced
   - Auto-close on correction: Yes
4. Click "Enable Auto-Trading"

Auto-Trading Engine Response:
1. Create auto_trading_config record (DB)
2. Start auto_trading_session (DB)
3. Add symbol to Symbol Monitor Worker queue
4. Subscribe to Market Data Service events for this symbol
5. Begin monitoring cycle
```

---

### **Step 2: Symbol Monitor Worker - Entry Signal Detection**

```python
# Auto-Trading Engine - Symbol Monitor Worker
async def symbol_monitor_worker():
    """Monitors all enabled symbols for entry opportunities"""

    while True:
        # 1. Get all enabled symbols
        configs = await get_enabled_auto_trading_configs()

        for config in configs:
            # 2. REQUEST MARKET DATA (from existing agent)
            quote = await market_data_service.get_latest_quote(config.symbol)

            # 3. REQUEST TECHNICAL ANALYSIS (from existing agent)
            analysis = await technical_analyst_service.analyze({
                'symbol': config.symbol,
                'timeframes': ['5m', '15m', '1h'],
                'patterns': ['all'],  # SMC + Elliott Wave
                'include_reasoning': True
            })

            # 4. EVALUATE ENTRY DECISION (Auto-Trading logic)
            decision = await evaluate_entry_signal(
                config=config,
                quote=quote,
                analysis=analysis
            )

            if decision.should_enter:
                # 5. REQUEST POSITION SIZING (from Executor Service)
                position_size = await executor_service.calculate_position_size({
                    'user_id': config.user_id,
                    'symbol': config.symbol,
                    'risk_percent': config.risk_per_trade_percent,
                    'entry_price': quote.price,
                    'stop_loss_percent': config.stop_loss_percent
                })

                # 6. VALIDATE TRADE (from Executor Service Risk Manager)
                validation = await executor_service.validate_trade({
                    'user_id': config.user_id,
                    'symbol': config.symbol,
                    'quantity': position_size.quantity,
                    'max_concurrent': config.max_concurrent_positions
                })

                if validation.approved:
                    # 7. EXECUTE TRADE (from Executor Service)
                    order = await executor_service.execute_market_order({
                        'user_id': config.user_id,
                        'symbol': config.symbol,
                        'side': decision.side,  # LONG or SHORT
                        'quantity': position_size.quantity,
                        'stop_loss': position_size.stop_loss_price,
                        'take_profit': position_size.take_profit_price,
                        'metadata': {
                            'auto_trade': True,
                            'session_id': config.session_id,
                            'signal_confidence': analysis.confidence
                        }
                    })

                    # 8. RECORD IN SESSION (Auto-Trading logic)
                    await record_trade_entry(config, order, analysis)

                    # 9. NOTIFY USER (via Notification Service)
                    await notification_service.send({
                        'user_id': config.user_id,
                        'type': 'AUTO_TRADE_ENTRY',
                        'symbol': config.symbol,
                        'message': f"Auto-trade opened: {decision.side} {config.symbol}"
                    })

        await asyncio.sleep(5)  # Check every 5 seconds
```

**Key Point:** Auto-Trading Engine CALLS existing agents, doesn't duplicate them!

---

### **Step 3: Position Monitor Worker - Autonomous Position Management**

```python
# Auto-Trading Engine - Position Monitor Worker
async def position_monitor_worker():
    """Monitors all auto-traded positions for exit opportunities"""

    while True:
        # 1. GET ALL AUTO-TRADED POSITIONS (from Trading Service)
        positions = await trading_service.get_positions({
            'auto_trade': True,
            'status': 'OPEN'
        })

        for position in positions:
            # 2. GET CURRENT MARKET PRICE (from Market Data Service)
            quote = await market_data_service.get_latest_quote(position.symbol)

            # 3. GET LATEST TECHNICAL ANALYSIS (from Technical Analyst)
            analysis = await technical_analyst_service.analyze({
                'symbol': position.symbol,
                'timeframes': ['5m', '15m', '1h'],
                'context': {
                    'position_entry_price': position.avg_entry_price,
                    'position_side': position.side
                }
            })

            # 4. CALCULATE CURRENT P&L (from Trading Service)
            pnl_data = await trading_service.calculate_position_pnl({
                'position_id': position.id,
                'current_price': quote.price
            })

            # 5. MAKE AUTONOMOUS EXIT DECISION (Auto-Trading logic)
            decision = await autonomous_exit_decision({
                'position': position,
                'quote': quote,
                'analysis': analysis,
                'pnl_data': pnl_data,
                'config': position.config
            })

            if decision.action == 'CLOSE':
                # 6. EXECUTE EXIT (from Executor Service)
                exit_order = await executor_service.close_position({
                    'position_id': position.id,
                    'reason': decision.reason,
                    'confidence': decision.confidence
                })

                # 7. RECORD IN SESSION (Auto-Trading logic)
                await record_trade_exit(position, exit_order, decision)

                # 8. NOTIFY USER (via Notification Service)
                await notification_service.send({
                    'user_id': position.user_id,
                    'type': 'AUTO_TRADE_EXIT',
                    'symbol': position.symbol,
                    'pnl': pnl_data.pnl,
                    'reason': decision.reason
                })

            elif decision.action == 'ADJUST_STOP':
                # 9. ADJUST STOP-LOSS (from Executor Service)
                await executor_service.update_stop_loss({
                    'position_id': position.id,
                    'new_stop_loss': decision.new_stop_loss,
                    'reason': 'TRAILING_STOP'
                })

        await asyncio.sleep(5)  # Check every 5 seconds
```

---

## 📋 What Each Component Does

### **AUTO-TRADING ENGINE (NEW)**
**Role:** Orchestration & Decision-Making
- Monitors enabled symbols
- Evaluates entry/exit signals
- Calls other agents for analysis
- Makes final trading decisions
- Tracks sessions & statistics
- Manages user configurations

**Does NOT:**
- ❌ Detect patterns (Technical Analyst does this)
- ❌ Execute orders directly (Executor does this)
- ❌ Calculate position sizes (Executor's Risk Manager does this)
- ❌ Store positions (Trading Service does this)
- ❌ Get market data (Market Data Service does this)

---

### **MARKET DATA SERVICE (EXISTING)**
**Role:** Real-Time Market Data
- WebSocket connections to Alpaca/Binance
- Real-time quote feeds
- Historical OHLCV data
- Tick storage in TimescaleDB

**Auto-Trading Integration:**
- Auto-Trading subscribes to quote updates
- Requests latest prices for positions
- Gets historical data for analysis context

---

### **TECHNICAL ANALYST SERVICE (EXISTING)**
**Role:** Pattern Detection & Analysis
- 21 algorithms (13 SMC + 8 Elliott Wave)
- Divergence detection
- Multi-timeframe analysis
- AI-powered reasoning

**Auto-Trading Integration:**
- Auto-Trading requests analysis for symbols
- Provides entry/exit signal recommendations
- Gives confidence scores
- Identifies market direction changes

---

### **EXECUTOR SERVICE (EXISTING)**
**Role:** Trade Execution & Risk Management
- Order Manager: Places orders with brokers
- Position Sizer: Calculates optimal position sizes
- Risk Manager: Validates trades against limits
- Broker API integration

**Auto-Trading Integration:**
- Auto-Trading calls for position sizing
- Requests trade validation
- Executes orders through Executor
- Updates stop-loss/take-profit levels

---

### **TRADING SERVICE (EXISTING)**
**Role:** Position & Order Tracking
- Stores all positions in database
- Tracks P&L
- Order history
- Portfolio management

**Auto-Trading Integration:**
- Auto-Trading queries open positions
- Records trades with auto_trade=true flag
- Gets P&L calculations
- Tracks session performance

---

### **ORCHESTRATOR SERVICE (EXISTING)**
**Role:** Multi-Agent Coordination
- Coordinates complex workflows
- Event routing
- Agent communication

**Auto-Trading Integration:**
- Could be enhanced to handle auto-trading workflows
- Or Auto-Trading Engine runs independently
- **Decision:** Auto-Trading Engine is self-contained orchestrator for autonomous trading

---

## 🆕 What We're Actually Building

### **1. Auto-Trading Engine Service**
**NEW Components:**
- `workers/symbol_monitor.py` - Monitors enabled symbols
- `workers/position_monitor.py` - Monitors open positions
- `workers/session_manager.py` - Manages sessions
- `services/decision_engine.py` - Entry/exit decision logic
- `services/session_service.py` - Session tracking
- `api/routes/config.py` - Configuration endpoints
- `repositories/config_repository.py` - DB access

**USES Existing:**
- `market_data_service` (quotes, historical)
- `technical_analyst_service` (analysis, patterns)
- `executor_service` (orders, risk, sizing)
- `trading_service` (positions, P&L)
- `notification_service` (alerts)

---

### **2. Database Schema (NEW)**
```sql
-- User configurations
CREATE TABLE auto_trading_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT false,
    risk_per_trade_percent DECIMAL(5,2) DEFAULT 1.0,
    max_concurrent_positions INTEGER DEFAULT 3,
    max_daily_loss_percent DECIMAL(5,2) DEFAULT 5.0,
    stop_loss_percent DECIMAL(5,2) DEFAULT 2.0,
    strategy_type VARCHAR(20) DEFAULT 'BALANCED',
    entry_confidence_threshold DECIMAL(5,2) DEFAULT 70.0,
    trading_start_hour INTEGER DEFAULT 0,
    trading_end_hour INTEGER DEFAULT 23,
    auto_close_on_correction BOOLEAN DEFAULT true,
    trailing_stop_enabled BOOLEAN DEFAULT true,
    trailing_stop_percent DECIMAL(5,2) DEFAULT 2.0,
    broker VARCHAR(50) NOT NULL,
    asset_class VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, symbol)
);

-- Active sessions
CREATE TABLE auto_trading_sessions (
    id UUID PRIMARY KEY,
    config_id UUID REFERENCES auto_trading_configs(id),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- ACTIVE, PAUSED, STOPPED
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,
    best_trade_pnl DECIMAL(20,8) DEFAULT 0,
    worst_trade_pnl DECIMAL(20,8) DEFAULT 0,
    current_open_positions INTEGER DEFAULT 0,
    daily_loss DECIMAL(20,8) DEFAULT 0,
    last_trade_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ,
    error_count INTEGER DEFAULT 0,
    last_error_message VARCHAR(500)
);

-- Decision audit trail
CREATE TABLE position_decisions (
    id UUID PRIMARY KEY,
    position_id UUID REFERENCES positions(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    current_price DECIMAL(20,8),
    pnl_percent DECIMAL(10,4),
    trend_direction VARCHAR(20),
    correction_probability DECIMAL(5,2),
    reversal_probability DECIMAL(5,2),
    action VARCHAR(20),  -- HOLD, CLOSE, ADJUST_STOP
    reason TEXT,
    confidence DECIMAL(5,2),
    executed BOOLEAN DEFAULT false,
    execution_price DECIMAL(20,8),
    execution_time TIMESTAMPTZ
);
```

---

### **3. Frontend UI (NEW)**
- Auto-Trading Dashboard
- Symbol selector with enable/disable toggles
- Risk parameter configuration
- Real-time session statistics
- AI decision visualization
- Position monitor with auto-close indicators

---

## 🔐 Modified Existing Services

### **Positions Table (Trading Service) - ADD FIELD**
```sql
ALTER TABLE positions ADD COLUMN auto_trade BOOLEAN DEFAULT false;
ALTER TABLE positions ADD COLUMN session_id UUID REFERENCES auto_trading_sessions(id);
```

### **Orders Table (Trading Service) - ADD FIELD**
```sql
ALTER TABLE orders ADD COLUMN auto_trade BOOLEAN DEFAULT false;
```

---

## ✅ Summary: What's New vs What We're Reusing

| Component | Status | Purpose |
|-----------|--------|---------|
| **Market Data Service** | ✅ EXISTING | Real-time quotes & historical data |
| **Technical Analyst** | ✅ EXISTING | Pattern detection & AI analysis |
| **Executor Service** | ✅ EXISTING | Order execution & risk management |
| **Trading Service** | ✅ EXISTING | Position/order tracking |
| **Notification Service** | ✅ EXISTING | User alerts |
| **Auto-Trading Engine** | ❌ NEW | Orchestrates autonomous trading |
| **Symbol Config UI** | ❌ NEW | Enable/disable symbols |
| **Background Workers** | ❌ NEW | 24/7 monitoring |
| **Decision Engine** | ❌ NEW | Entry/exit logic |
| **Session Tracking** | ❌ NEW | Auto-trading statistics |
| **Auto-Trading DB Schema** | ❌ NEW | Configs, sessions, decisions |

---

## 🎯 Conclusion

The Auto-Trading Engine is a **lightweight orchestration layer** that:
1. Manages user configurations
2. Runs background monitoring workers
3. Makes autonomous decisions
4. CALLS existing agents for actual work
5. Tracks sessions and statistics

**No duplication. Maximum leverage of existing capabilities.**

Does this architecture make more sense? 🚀
