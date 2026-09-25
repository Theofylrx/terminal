# Auto-Trading Engine Architecture

**Feature:** Fully Autonomous AI Trading System
**Status:** Design Phase
**Priority:** Critical

---

## 🎯 Overview

Transform Terminal from manual trading platform to **fully autonomous AI trading system** where:
- Users select symbols to monitor
- System trades automatically based on AI signals
- Operates 24/7 even when user is offline
- Manages positions intelligently with risk management
- Makes autonomous decisions to maximize profit and minimize loss

---

## 🏗️ New System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS TRADING LAYER                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│   User Config    │         │  Auto-Trading    │         │  Risk Manager    │
│   Dashboard      │────────→│     Engine       │────────→│    Service       │
│                  │         │                  │         │                  │
│ Enable Symbols   │         │ • Strategy       │         │ • Position Size  │
│ Set Risk Params  │         │ • Signal Eval    │         │ • Stop Loss      │
│ Trading Hours    │         │ • Entry Logic    │         │ • Take Profit    │
└──────────────────┘         │ • Exit Logic     │         │ • Risk/Reward    │
                             └──────────────────┘         └──────────────────┘
                                      │                            │
                                      ↓                            ↓
                             ┌──────────────────────────────────────────┐
                             │      Position Monitor (Background)       │
                             │                                          │
                             │  Continuously monitors all open          │
                             │  positions and market conditions         │
                             └──────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
           ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
           │ Market Data    │  │  Technical     │  │   Trading      │
           │   Service      │  │   Analyst      │  │   Service      │
           │                │  │                │  │                │
           │ Real-time      │  │ Pattern        │  │ Execute        │
           │ Prices         │  │ Detection      │  │ Orders         │
           └────────────────┘  └────────────────┘  └────────────────┘
```

---

## 📋 Required Components

### **1. Auto-Trading Engine Service** (NEW)

**Purpose:** Core decision-making engine for autonomous trading

**Responsibilities:**
- Monitor enabled symbols continuously
- Aggregate signals from Technical Analyst
- Evaluate entry opportunities
- Execute trade entries automatically
- Hand off positions to Position Monitor

**Key Functions:**
```python
async def monitor_symbols():
    """Continuously monitor all enabled symbols"""

async def evaluate_entry_signal(symbol, signal):
    """Decide if signal warrants trade entry"""

async def execute_entry(symbol, signal, user_config):
    """Open position automatically"""

async def calculate_position_size(user_config, signal):
    """Determine trade size based on risk parameters"""
```

**Database Tables:**
```sql
-- User auto-trading configuration
CREATE TABLE auto_trading_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    enabled BOOLEAN DEFAULT false,

    -- Risk parameters
    risk_per_trade_percent DECIMAL(5,2) DEFAULT 1.0,
    max_concurrent_positions INTEGER DEFAULT 3,
    max_daily_loss_percent DECIMAL(5,2) DEFAULT 5.0,

    -- Strategy settings
    strategy_type VARCHAR(50) DEFAULT 'balanced',  -- aggressive, balanced, conservative
    entry_confidence_threshold DECIMAL(5,2) DEFAULT 70.0,

    -- Trading hours
    trading_start_hour INTEGER DEFAULT 0,
    trading_end_hour INTEGER DEFAULT 23,

    -- Auto-management settings
    auto_close_on_correction BOOLEAN DEFAULT true,
    trailing_stop_enabled BOOLEAN DEFAULT true,
    trailing_stop_percent DECIMAL(5,2) DEFAULT 2.0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, symbol)
);

-- Active auto-trading sessions
CREATE TABLE auto_trading_sessions (
    id UUID PRIMARY KEY,
    config_id UUID REFERENCES auto_trading_configs(id),
    user_id UUID REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- ACTIVE, PAUSED, STOPPED

    -- Session stats
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    total_pnl DECIMAL(20,8) DEFAULT 0,

    started_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ
);
```

---

### **2. Position Monitor Service** (NEW)

**Purpose:** Background worker that monitors ALL open positions 24/7

**Responsibilities:**
- Monitor all auto-traded positions continuously
- Consult Technical Analyst for market direction changes
- Detect correction signals
- Make autonomous exit decisions
- Execute exits automatically

**Key Functions:**
```python
async def monitor_all_positions():
    """
    Background task running continuously
    Checks every open auto-traded position
    """
    while True:
        positions = await get_all_auto_positions()

        for position in positions:
            await analyze_position(position)

        await asyncio.sleep(5)  # Check every 5 seconds

async def analyze_position(position):
    """
    Intelligent position analysis

    Steps:
    1. Get current price
    2. Calculate current P&L
    3. Get latest market signals
    4. Consult Technical Analyst
    5. Make decision (hold, close, adjust)
    6. Execute decision
    """

    # Get current market data
    current_price = await market_data_service.get_quote(position.symbol)

    # Calculate P&L
    pnl_percent = calculate_pnl_percent(position, current_price)

    # Get latest signals
    signals = await technical_analyst.get_latest_signals(
        symbol=position.symbol,
        timeframe='15m'
    )

    # Decision logic
    decision = await make_autonomous_decision(
        position=position,
        current_price=current_price,
        pnl_percent=pnl_percent,
        signals=signals
    )

    # Execute decision
    if decision.action == 'CLOSE':
        await close_position(position, decision.reason)
    elif decision.action == 'ADJUST_STOP':
        await adjust_stop_loss(position, decision.new_stop_loss)
    elif decision.action == 'HOLD':
        pass  # Continue monitoring

async def make_autonomous_decision(position, current_price, pnl_percent, signals):
    """
    AI Decision Engine

    Scenarios:

    1. In Profit + Correction Detected:
       → Close position, take profit

    2. In Profit + Trend Continues:
       → Hold, adjust trailing stop

    3. In Loss + Reversal Likely:
       → Hold, market may recover

    4. In Loss + No Recovery Signal:
       → Cut loss, exit position

    5. In Loss + Strong Downtrend:
       → Immediate exit
    """

    # Get market direction
    direction = signals.get('trend_direction')  # BULLISH, BEARISH, NEUTRAL
    correction_detected = signals.get('correction_probability', 0) > 0.7
    reversal_likely = signals.get('reversal_probability', 0) > 0.6

    # Decision tree
    if pnl_percent > 0:  # In profit
        if correction_detected:
            return Decision(
                action='CLOSE',
                reason='PROFIT_PROTECTION_CORRECTION_DETECTED',
                confidence=0.9
            )
        elif direction == 'BULLISH' and position.side == 'LONG':
            return Decision(
                action='ADJUST_STOP',
                new_stop_loss=calculate_trailing_stop(current_price, 0.02),
                reason='TREND_CONTINUES_TRAIL_STOP'
            )
        else:
            return Decision(action='HOLD', reason='MONITORING')

    else:  # In loss
        if not reversal_likely and abs(pnl_percent) > position.config.max_loss_percent:
            return Decision(
                action='CLOSE',
                reason='STOP_LOSS_NO_RECOVERY_SIGNAL',
                confidence=0.8
            )
        elif reversal_likely:
            return Decision(
                action='HOLD',
                reason='POTENTIAL_REVERSAL_DETECTED'
            )
        elif direction == 'BEARISH' and position.side == 'LONG':
            return Decision(
                action='CLOSE',
                reason='STRONG_OPPOSITE_TREND',
                confidence=0.85
            )
        else:
            return Decision(action='HOLD', reason='WITHIN_RISK_TOLERANCE')
```

---

### **3. Risk Manager Service** (NEW)

**Purpose:** Centralized risk management for all auto-trading

**Responsibilities:**
- Calculate position sizes based on risk parameters
- Validate trades don't exceed risk limits
- Monitor total portfolio exposure
- Prevent over-trading
- Emergency shutdown on excessive losses

**Key Functions:**
```python
async def calculate_position_size(user_id, symbol, entry_price, config):
    """
    Calculate position size based on risk parameters

    Example:
    - User capital: $10,000
    - Risk per trade: 1%
    - Risk amount: $100
    - Stop loss: 2% from entry
    - Position size: $100 / 0.02 = $5,000 (50% of capital)
    """
    user_capital = await get_user_capital(user_id)
    risk_amount = user_capital * (config.risk_per_trade_percent / 100)

    stop_loss_percent = config.stop_loss_percent / 100
    position_size = risk_amount / stop_loss_percent

    # Ensure position size doesn't exceed limits
    max_position_size = user_capital * 0.5  # Max 50% per position
    position_size = min(position_size, max_position_size)

    return {
        'quantity': position_size / entry_price,
        'position_value': position_size,
        'risk_amount': risk_amount
    }

async def validate_trade(user_id, proposed_trade):
    """
    Validate trade against risk limits

    Checks:
    1. User has sufficient capital
    2. Won't exceed max concurrent positions
    3. Won't exceed daily loss limit
    4. Won't exceed total exposure limit
    """

    # Check capital
    user_capital = await get_user_capital(user_id)
    if proposed_trade.required_capital > user_capital:
        return ValidationResult(valid=False, reason='INSUFFICIENT_CAPITAL')

    # Check concurrent positions
    open_positions = await get_open_positions_count(user_id)
    config = await get_auto_trading_config(user_id, proposed_trade.symbol)

    if open_positions >= config.max_concurrent_positions:
        return ValidationResult(valid=False, reason='MAX_POSITIONS_REACHED')

    # Check daily loss
    daily_loss = await get_daily_loss(user_id)
    max_daily_loss = user_capital * (config.max_daily_loss_percent / 100)

    if daily_loss >= max_daily_loss:
        return ValidationResult(valid=False, reason='DAILY_LOSS_LIMIT_REACHED')

    return ValidationResult(valid=True)

async def emergency_shutdown(user_id, reason):
    """
    Emergency shutdown of all auto-trading

    Triggered when:
    - Daily loss limit exceeded
    - Critical error detected
    - Unusual market conditions
    """

    # Disable all auto-trading configs
    await disable_all_auto_trading(user_id)

    # Close all open positions at market
    await close_all_positions(user_id, reason='EMERGENCY_SHUTDOWN')

    # Notify user
    await send_notification(user_id, {
        'type': 'EMERGENCY_SHUTDOWN',
        'reason': reason,
        'timestamp': datetime.utcnow()
    })
```

---

### **4. Frontend UI Components** (NEW)

**Auto-Trading Configuration Dashboard:**

```javascript
// Component: AutoTradingConfig.tsx

interface SymbolConfig {
  symbol: string;
  enabled: boolean;
  strategyType: 'aggressive' | 'balanced' | 'conservative';
  riskPerTrade: number;  // percentage
  maxPositions: number;
  autoCloseOnCorrection: boolean;
  trailingStopEnabled: boolean;
  trailingStopPercent: number;
}

function AutoTradingDashboard() {
  return (
    <div>
      <h1>Auto-Trading Configuration</h1>

      {/* Symbol Selection */}
      <SymbolSelector
        availableSymbols={availableSymbols}
        onSymbolToggle={handleSymbolToggle}
      />

      {/* Enabled Symbols */}
      <EnabledSymbolsList>
        {enabledSymbols.map(symbol => (
          <SymbolCard
            key={symbol}
            symbol={symbol}
            status={autoTradingStatus[symbol]}
            stats={sessionStats[symbol]}
            onDisable={() => disableSymbol(symbol)}
            onConfigure={() => openConfig(symbol)}
          />
        ))}
      </EnabledSymbolsList>

      {/* Risk Parameters */}
      <RiskConfiguration
        riskPerTrade={config.riskPerTrade}
        maxConcurrentPositions={config.maxPositions}
        maxDailyLoss={config.maxDailyLoss}
        onChange={updateRiskParams}
      />

      {/* Strategy Settings */}
      <StrategySelector
        selected={config.strategyType}
        options={['aggressive', 'balanced', 'conservative']}
        onChange={updateStrategy}
      />

      {/* Active Positions Monitor */}
      <ActivePositionsMonitor
        positions={activePositions}
        showAIDecisions={true}
      />
    </div>
  );
}
```

**Symbol Card Component:**
```javascript
function SymbolCard({ symbol, status, stats, onDisable, onConfigure }) {
  return (
    <Card>
      <CardHeader>
        <h3>{symbol}</h3>
        <StatusBadge status={status} />  {/* ACTIVE, PAUSED, MONITORING */}
        <Switch
          checked={status === 'ACTIVE'}
          onChange={onDisable}
        />
      </CardHeader>

      <CardBody>
        {/* Session Stats */}
        <Stats>
          <Stat label="Trades" value={stats.totalTrades} />
          <Stat label="Win Rate" value={`${stats.winRate}%`} />
          <Stat label="P&L" value={stats.totalPnL} color={stats.totalPnL > 0 ? 'green' : 'red'} />
        </Stats>

        {/* Current Signal */}
        <CurrentSignal symbol={symbol} />

        {/* Next Action */}
        <AIDecision symbol={symbol} />
      </CardBody>

      <CardFooter>
        <Button onClick={onConfigure}>Configure</Button>
        <Button variant="danger" onClick={onDisable}>Disable</Button>
      </CardFooter>
    </Card>
  );
}
```

---

## 🔄 Complete Autonomous Trading Flow

### **Step 1: User Enables Symbol**

```
User Action:
1. Navigate to Auto-Trading dashboard
2. Select symbol (e.g., AAPL)
3. Configure risk parameters:
   - Risk per trade: 1%
   - Max positions: 3
   - Strategy: Balanced
   - Auto-close on correction: Yes
4. Click "Enable Auto-Trading"

System Response:
1. Create auto_trading_config record
2. Start auto_trading_session
3. Add symbol to monitoring queue
4. Subscribe to market data feed
5. Begin signal evaluation
```

### **Step 2: Signal Detection & Entry**

```
Auto-Trading Engine (Running 24/7):

Every 5 seconds:
1. Check market data for enabled symbols
2. Query Technical Analyst for latest signals
3. Evaluate entry conditions

When Signal Detected:
1. Signal: BULLISH pattern on AAPL (confidence: 85%)
2. Validate signal against entry threshold (>70%)
3. Calculate position size via Risk Manager
4. Validate trade won't exceed risk limits
5. Execute market buy order
6. Record trade in database
7. Hand off to Position Monitor
8. Notify user (optional)
```

**Code Example:**
```python
async def signal_detected_handler(symbol, signal):
    """Handle new signal from Technical Analyst"""

    # Get user configs for this symbol
    configs = await get_enabled_configs(symbol)

    for config in configs:
        # Check if signal meets threshold
        if signal.confidence < config.entry_confidence_threshold:
            continue

        # Check if within trading hours
        if not is_within_trading_hours(config):
            continue

        # Calculate position size
        position_size = await risk_manager.calculate_position_size(
            user_id=config.user_id,
            symbol=symbol,
            entry_price=signal.entry_price,
            config=config
        )

        # Validate trade
        validation = await risk_manager.validate_trade(
            user_id=config.user_id,
            proposed_trade=position_size
        )

        if not validation.valid:
            logger.info(f"Trade rejected: {validation.reason}")
            continue

        # Execute trade
        order = await trading_service.create_market_order(
            user_id=config.user_id,
            symbol=symbol,
            side='BUY' if signal.direction == 'BULLISH' else 'SELL',
            quantity=position_size.quantity,
            metadata={
                'auto_trade': True,
                'signal_id': signal.id,
                'confidence': signal.confidence
            }
        )

        # Track position
        await position_monitor.add_position(
            order_id=order.id,
            config_id=config.id,
            entry_signal=signal
        )

        logger.info(f"Auto-trade executed: {order.id}")
```

### **Step 3: Position Monitoring (24/7)**

```
Position Monitor Background Worker:

Continuously (every 5 seconds):
1. Get all open auto-traded positions
2. For each position:
   a. Get current price
   b. Calculate current P&L
   c. Get latest market signals
   d. Consult Technical Analyst
   e. Make autonomous decision
   f. Execute decision

Example Scenario 1: Profit Protection
- Position: LONG AAPL at $150
- Current Price: $155 (+3.33% profit)
- Signal: Correction probability 75%
- Decision: Close position, take profit
- Action: Execute market sell order

Example Scenario 2: Let It Run
- Position: LONG AAPL at $150
- Current Price: $156 (+4% profit)
- Signal: Strong bullish trend continues
- Decision: Adjust trailing stop-loss
- Action: Update stop from $148 to $153 (2% trail)

Example Scenario 3: Cut Loss
- Position: LONG AAPL at $150
- Current Price: $147 (-2% loss)
- Signal: Strong bearish trend, no reversal
- Decision: Cut loss before it deepens
- Action: Execute market sell order
```

**Code Example:**
```python
async def position_monitor_worker():
    """Background worker running 24/7"""

    logger.info("Position Monitor started")

    while True:
        try:
            # Get all auto-traded positions
            positions = await get_all_auto_positions(status='OPEN')

            logger.debug(f"Monitoring {len(positions)} positions")

            for position in positions:
                try:
                    await analyze_and_act(position)
                except Exception as e:
                    logger.error(f"Error analyzing position {position.id}: {e}")

            # Sleep for 5 seconds
            await asyncio.sleep(5)

        except Exception as e:
            logger.error(f"Position monitor error: {e}")
            await asyncio.sleep(10)  # Longer sleep on error

async def analyze_and_act(position):
    """Analyze position and take autonomous action"""

    # Get current market data
    quote = await market_data_service.get_quote(position.symbol)
    current_price = quote.price

    # Calculate P&L
    if position.side == 'LONG':
        pnl_percent = ((current_price - position.entry_price) / position.entry_price) * 100
    else:  # SHORT
        pnl_percent = ((position.entry_price - current_price) / position.entry_price) * 100

    # Get latest signals (multiple timeframes)
    signals = await technical_analyst.get_comprehensive_analysis(
        symbol=position.symbol,
        timeframes=['5m', '15m', '1h']
    )

    # Make decision
    decision = await decision_engine.evaluate(
        position=position,
        current_price=current_price,
        pnl_percent=pnl_percent,
        signals=signals,
        config=position.config
    )

    # Log decision
    await log_decision(position, decision)

    # Execute action
    if decision.action == 'CLOSE':
        await execute_close(position, decision)
    elif decision.action == 'ADJUST_STOP':
        await execute_adjust_stop(position, decision)
    elif decision.action == 'HOLD':
        pass  # Continue monitoring

    # Update position metadata
    await update_position_analysis(position, {
        'last_check': datetime.utcnow(),
        'current_pnl_percent': pnl_percent,
        'last_decision': decision.action,
        'last_decision_reason': decision.reason
    })
```

### **Step 4: Automatic Exit**

```
Decision Engine determines exit is optimal:

Scenario: Position in profit, correction detected

1. Current State:
   - Position: LONG BTCUSDT
   - Entry: $45,000
   - Current: $47,250 (+5% profit)
   - P&L: $1,125

2. Market Analysis:
   - Signal: Bearish divergence detected
   - Correction probability: 82%
   - Support level: $46,500

3. Decision:
   - Action: CLOSE
   - Reason: PROTECT_PROFIT_CORRECTION_DETECTED
   - Confidence: 88%

4. Execution:
   - Execute market sell order
   - Close position
   - Realize profit: $1,125
   - Update user capital
   - Record in trade history
   - Update session stats
   - Continue monitoring other symbols
```

---

## 📊 Database Schema Updates

```sql
-- Additional tables needed

CREATE TABLE position_decisions (
    id UUID PRIMARY KEY,
    position_id UUID REFERENCES positions(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Market state
    current_price DECIMAL(20,8),
    pnl_percent DECIMAL(10,4),

    -- Signals
    trend_direction VARCHAR(20),
    correction_probability DECIMAL(5,2),
    reversal_probability DECIMAL(5,2),

    -- Decision
    action VARCHAR(20),  -- HOLD, CLOSE, ADJUST_STOP
    reason TEXT,
    confidence DECIMAL(5,2),

    -- Execution
    executed BOOLEAN DEFAULT false,
    execution_price DECIMAL(20,8),
    execution_time TIMESTAMPTZ
);

CREATE INDEX idx_position_decisions_position ON position_decisions(position_id);
CREATE INDEX idx_position_decisions_timestamp ON position_decisions(timestamp);
```

---

## 🚀 Implementation Plan

### **Phase 1: Core Infrastructure** (Week 1-2)
- [ ] Create Auto-Trading Engine service
- [ ] Build database schema
- [ ] Implement Risk Manager
- [ ] Create background worker framework

### **Phase 2: Decision Engine** (Week 3-4)
- [ ] Build decision algorithm
- [ ] Implement signal aggregation
- [ ] Create position analyzer
- [ ] Test decision logic

### **Phase 3: Position Monitor** (Week 5-6)
- [ ] Build background monitor worker
- [ ] Implement 24/7 monitoring
- [ ] Create autonomous exit logic
- [ ] Add trailing stop-loss

### **Phase 4: Frontend UI** (Week 7-8)
- [ ] Build symbol selection interface
- [ ] Create configuration dashboard
- [ ] Add real-time position monitor
- [ ] Build AI decision visualization

### **Phase 5: Testing & Optimization** (Week 9-10)
- [ ] Paper trading validation
- [ ] Performance optimization
- [ ] Edge case handling
- [ ] Load testing

---

## ⚠️ Critical Considerations

### **1. Fail-Safe Mechanisms**
- Emergency shutdown on excessive loss
- Circuit breaker for market anomalies
- Automatic disabling on repeated failures
- Manual override always available

### **2. Notification System**
- Alert on position entry
- Notify on automatic exits
- Daily performance summary
- Emergency alerts (SMS/Email)

### **3. Audit Trail**
- Log every decision
- Record reasoning
- Track performance
- Enable backtesting

---

**Does this architecture align with your vision?**

This is a massive but essential feature. Should we proceed with implementation?
