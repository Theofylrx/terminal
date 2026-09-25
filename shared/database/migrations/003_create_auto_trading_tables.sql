-- Migration: Create Auto-Trading Tables
-- Date: 2024-01-20
-- Description: Create tables for autonomous trading system

-- ============================================================================
-- AUTO-TRADING CONFIGURATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS auto_trading_configs (
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
    strategy_type VARCHAR(20) DEFAULT 'BALANCED' NOT NULL,
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

    -- Constraints
    CONSTRAINT unique_user_symbol UNIQUE(user_id, symbol),
    CONSTRAINT valid_risk_percent CHECK (risk_per_trade_percent >= 0.1 AND risk_per_trade_percent <= 5.0),
    CONSTRAINT valid_max_positions CHECK (max_concurrent_positions >= 1 AND max_concurrent_positions <= 10),
    CONSTRAINT valid_daily_loss CHECK (max_daily_loss_percent >= 1.0 AND max_daily_loss_percent <= 15.0),
    CONSTRAINT valid_stop_loss CHECK (stop_loss_percent >= 0.5 AND stop_loss_percent <= 10.0),
    CONSTRAINT valid_strategy CHECK (strategy_type IN ('AGGRESSIVE', 'BALANCED', 'CONSERVATIVE')),
    CONSTRAINT valid_confidence CHECK (entry_confidence_threshold >= 50.0 AND entry_confidence_threshold <= 95.0),
    CONSTRAINT valid_trading_hours CHECK (trading_start_hour >= 0 AND trading_start_hour <= 23 AND trading_end_hour >= 0 AND trading_end_hour <= 23),
    CONSTRAINT valid_trailing_stop CHECK (trailing_stop_percent >= 0.5 AND trailing_stop_percent <= 5.0)
);

-- Indexes for auto_trading_configs
CREATE INDEX idx_auto_trading_configs_user ON auto_trading_configs(user_id);
CREATE INDEX idx_auto_trading_configs_symbol ON auto_trading_configs(symbol);
CREATE INDEX idx_auto_trading_configs_enabled ON auto_trading_configs(enabled);
CREATE INDEX idx_auto_trading_configs_user_enabled ON auto_trading_configs(user_id, enabled);

-- ============================================================================
-- AUTO-TRADING SESSIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS auto_trading_sessions (
    id VARCHAR(36) PRIMARY KEY,
    config_id VARCHAR(36) NOT NULL REFERENCES auto_trading_configs(id) ON DELETE CASCADE,
    user_id VARCHAR(36) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL,

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
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_session_status CHECK (status IN ('ACTIVE', 'PAUSED', 'STOPPED', 'ERROR'))
);

-- Indexes for auto_trading_sessions
CREATE INDEX idx_auto_trading_sessions_config ON auto_trading_sessions(config_id);
CREATE INDEX idx_auto_trading_sessions_user ON auto_trading_sessions(user_id);
CREATE INDEX idx_auto_trading_sessions_symbol ON auto_trading_sessions(symbol);
CREATE INDEX idx_auto_trading_sessions_status ON auto_trading_sessions(status);
CREATE INDEX idx_auto_trading_sessions_user_status ON auto_trading_sessions(user_id, status);
CREATE INDEX idx_auto_trading_sessions_active ON auto_trading_sessions(status, last_activity_at) WHERE status = 'ACTIVE';

-- ============================================================================
-- POSITION DECISIONS TABLE (Audit Trail)
-- ============================================================================

CREATE TABLE IF NOT EXISTS position_decisions (
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
    action VARCHAR(20) NOT NULL,
    reason TEXT NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,

    -- Execution
    executed BOOLEAN DEFAULT false NOT NULL,
    execution_price DECIMAL(20,8),
    execution_time TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Constraints
    CONSTRAINT valid_decision_action CHECK (action IN ('HOLD', 'CLOSE', 'ADJUST_STOP'))
);

-- Indexes for position_decisions
CREATE INDEX idx_position_decisions_position ON position_decisions(position_id);
CREATE INDEX idx_position_decisions_timestamp ON position_decisions(timestamp DESC);
CREATE INDEX idx_position_decisions_action ON position_decisions(action);
CREATE INDEX idx_position_decisions_executed ON position_decisions(executed);

-- ============================================================================
-- UPDATE TRIGGERS FOR updated_at
-- ============================================================================

-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for auto_trading_configs
DROP TRIGGER IF EXISTS update_auto_trading_configs_updated_at ON auto_trading_configs;
CREATE TRIGGER update_auto_trading_configs_updated_at
    BEFORE UPDATE ON auto_trading_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for auto_trading_sessions
DROP TRIGGER IF EXISTS update_auto_trading_sessions_updated_at ON auto_trading_sessions;
CREATE TRIGGER update_auto_trading_sessions_updated_at
    BEFORE UPDATE ON auto_trading_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE auto_trading_configs IS 'User configurations for autonomous trading on specific symbols';
COMMENT ON TABLE auto_trading_sessions IS 'Active and historical auto-trading sessions with statistics';
COMMENT ON TABLE position_decisions IS 'Audit trail of AI decisions for position management';

COMMENT ON COLUMN auto_trading_configs.enabled IS 'Whether auto-trading is currently active for this symbol';
COMMENT ON COLUMN auto_trading_configs.risk_per_trade_percent IS 'Percentage of capital to risk per trade (0.1-5.0%)';
COMMENT ON COLUMN auto_trading_configs.max_concurrent_positions IS 'Maximum number of open positions allowed (1-10)';
COMMENT ON COLUMN auto_trading_configs.entry_confidence_threshold IS 'Minimum AI confidence required to enter trade (50-95%)';
COMMENT ON COLUMN auto_trading_configs.auto_close_on_correction IS 'Automatically close profitable positions when correction detected';
COMMENT ON COLUMN auto_trading_configs.trailing_stop_enabled IS 'Enable trailing stop-loss adjustments';

COMMENT ON COLUMN auto_trading_sessions.status IS 'Session status: ACTIVE (running), PAUSED (temp stop), STOPPED (ended), ERROR (failed)';
COMMENT ON COLUMN auto_trading_sessions.daily_loss IS 'Accumulated loss for current trading day';
COMMENT ON COLUMN auto_trading_sessions.total_pnl IS 'Total profit/loss for this session';

-- ============================================================================
-- VERIFY MIGRATION
-- ============================================================================

-- Show created tables
SELECT
    tablename,
    schemaname
FROM pg_tables
WHERE tablename IN ('auto_trading_configs', 'auto_trading_sessions', 'position_decisions')
ORDER BY tablename;

-- Show indexes
SELECT
    tablename,
    indexname
FROM pg_indexes
WHERE tablename IN ('auto_trading_configs', 'auto_trading_sessions', 'position_decisions')
ORDER BY tablename, indexname;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 003 completed successfully: Auto-Trading tables created';
END $$;
