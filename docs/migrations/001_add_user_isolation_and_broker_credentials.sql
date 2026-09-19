-- Migration: Add User Isolation and Broker Credential Support
-- Date: 2024-09-19
-- Description: Adds user_id columns to all user-specific tables and creates broker_credentials table
-- Status: CRITICAL SECURITY FIX - Multi-Tenant Isolation

-- ==============================================================================
-- CRITICAL: This migration adds user_id to tables for multi-tenant isolation
-- ==============================================================================

BEGIN;

-- ==============================================================================
-- 1. ADD user_id TO signals TABLE
-- ==============================================================================

-- Add user_id column (nullable initially for existing data)
ALTER TABLE signals
ADD COLUMN IF NOT EXISTS user_id UUID;

-- Add trading_decision_id for linking to trading decisions
ALTER TABLE signals
ADD COLUMN IF NOT EXISTS trading_decision_id UUID;

-- For existing signals, assign to a default user or mark for deletion
-- WARNING: Update this with your actual default user ID or handle existing data appropriately
-- UPDATE signals SET user_id = 'default-user-id-here' WHERE user_id IS NULL;

-- Make user_id NOT NULL after data migration
-- ALTER TABLE signals ALTER COLUMN user_id SET NOT NULL;

-- Add foreign key constraint
ALTER TABLE signals
ADD CONSTRAINT fk_signal_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- Add foreign key to trading_decisions
ALTER TABLE signals
ADD CONSTRAINT fk_signal_trading_decision
FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE SET NULL;

-- Add indexes for performance (user_id must be first for query optimization)
CREATE INDEX IF NOT EXISTS idx_signal_user_id ON signals(user_id);
CREATE INDEX IF NOT EXISTS idx_signal_user_symbol_timeframe ON signals(user_id, symbol, timeframe);

-- Drop old index if it exists and recreate with user_id
DROP INDEX IF EXISTS idx_signal_symbol_timeframe;

COMMENT ON COLUMN signals.user_id IS 'CRITICAL: User isolation - all queries MUST filter by this';

-- ==============================================================================
-- 2. CREATE trading_decisions TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS trading_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User ownership - CRITICAL for multi-user isolation
    user_id UUID NOT NULL,

    -- Basic information
    symbol VARCHAR(20) NOT NULL,
    action VARCHAR(10) NOT NULL CHECK (action IN ('BUY', 'SELL', 'WAIT', 'CLOSE')),
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    confidence_level VARCHAR(20) NOT NULL CHECK (confidence_level IN ('VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH')),

    -- Decision metadata
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP,
    should_trade VARCHAR(10) NOT NULL CHECK (should_trade IN ('true', 'false')),

    -- Arguments (stored as JSON)
    primary_arguments JSONB NOT NULL,
    counter_arguments JSONB NOT NULL,

    -- Fundamental alignment (stored as JSON)
    fundamental_alignment JSONB,

    -- Risk assessment (stored as JSON)
    risk_assessment JSONB NOT NULL,

    -- Entry plan (stored as JSON)
    entry_plan JSONB,

    -- Timeframe summary (stored as JSON)
    timeframe_summary JSONB NOT NULL,

    -- Confidence breakdown (stored as JSON)
    confidence_breakdown JSONB NOT NULL,

    -- Reasoning narratives (stored as TEXT - can be large)
    executive_summary TEXT NOT NULL,
    detailed_reasoning TEXT NOT NULL,

    -- Performance tracking (updated after trade completes)
    actual_entry_price FLOAT,
    actual_exit_price FLOAT,
    actual_pnl FLOAT,
    actual_pnl_percent FLOAT,
    trade_outcome VARCHAR(20) CHECK (trade_outcome IN ('WIN', 'LOSS', 'BREAKEVEN')),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key
    CONSTRAINT fk_trading_decision_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indexes for trading_decisions
CREATE INDEX IF NOT EXISTS idx_trading_decision_user_id ON trading_decisions(user_id);
CREATE INDEX IF NOT EXISTS idx_trading_decision_user_symbol ON trading_decisions(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_trading_decision_symbol ON trading_decisions(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_decision_action ON trading_decisions(action);
CREATE INDEX IF NOT EXISTS idx_trading_decision_confidence ON trading_decisions(confidence);
CREATE INDEX IF NOT EXISTS idx_trading_decision_generated_at ON trading_decisions(generated_at);
CREATE INDEX IF NOT EXISTS idx_trading_decision_should_trade ON trading_decisions(should_trade);

COMMENT ON TABLE trading_decisions IS 'Complete trading decisions with full evidence-based reasoning';
COMMENT ON COLUMN trading_decisions.user_id IS 'CRITICAL: User isolation - all queries MUST filter by this';

-- ==============================================================================
-- 3. CREATE evidence TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User ownership - CRITICAL for multi-user isolation
    user_id UUID NOT NULL,

    -- Link to trading decision
    trading_decision_id UUID NOT NULL,

    -- Evidence details
    source VARCHAR(100) NOT NULL,  -- "4H Timeframe", "Fundamental Analysis"
    type VARCHAR(100) NOT NULL,    -- "SMC Pattern", "Elliott Wave", "Indicator"
    description TEXT NOT NULL,
    score FLOAT NOT NULL,
    confidence FLOAT NOT NULL,
    timestamp TIMESTAMP,

    -- Evidence metadata (stored as JSON for flexibility)
    metadata JSONB,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign keys
    CONSTRAINT fk_evidence_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    CONSTRAINT fk_evidence_trading_decision
    FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE CASCADE
);

-- Indexes for evidence
CREATE INDEX IF NOT EXISTS idx_evidence_user_id ON evidence(user_id);
CREATE INDEX IF NOT EXISTS idx_evidence_user_decision ON evidence(user_id, trading_decision_id);
CREATE INDEX IF NOT EXISTS idx_evidence_decision_id ON evidence(trading_decision_id);
CREATE INDEX IF NOT EXISTS idx_evidence_source ON evidence(source);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidence(type);
CREATE INDEX IF NOT EXISTS idx_evidence_score ON evidence(score);

COMMENT ON TABLE evidence IS 'Evidence items supporting trading decisions for audit trail';
COMMENT ON COLUMN evidence.user_id IS 'CRITICAL: User isolation - all queries MUST filter by this';

-- ==============================================================================
-- 4. CREATE analysis_reports TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS analysis_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User ownership - CRITICAL for multi-user isolation
    user_id UUID NOT NULL,

    -- Link to trading decision
    trading_decision_id UUID NOT NULL,

    -- Report metadata
    symbol VARCHAR(20) NOT NULL,
    report_type VARCHAR(50) NOT NULL,  -- "MULTI_TIMEFRAME", "SINGLE_TIMEFRAME"
    timeframes_analyzed JSONB NOT NULL,  -- ["15M", "1H", "4H", "Daily"]

    -- Complete analysis data (stored as JSON)
    analysis_data JSONB NOT NULL,

    -- Report file path (if saved to disk)
    report_file_path VARCHAR(500),

    -- Generated timestamp
    generated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign keys
    CONSTRAINT fk_analysis_report_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    CONSTRAINT fk_analysis_report_trading_decision
    FOREIGN KEY (trading_decision_id) REFERENCES trading_decisions(id) ON DELETE CASCADE
);

-- Indexes for analysis_reports
CREATE INDEX IF NOT EXISTS idx_analysis_report_user_id ON analysis_reports(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_report_user_symbol ON analysis_reports(user_id, symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_report_decision_id ON analysis_reports(trading_decision_id);
CREATE INDEX IF NOT EXISTS idx_analysis_report_symbol ON analysis_reports(symbol);
CREATE INDEX IF NOT EXISTS idx_analysis_report_generated_at ON analysis_reports(generated_at);

COMMENT ON TABLE analysis_reports IS 'Complete multi-timeframe analysis reports for archival';
COMMENT ON COLUMN analysis_reports.user_id IS 'CRITICAL: User isolation - all queries MUST filter by this';

-- ==============================================================================
-- 5. CREATE broker_credentials TABLE
-- ==============================================================================

CREATE TABLE IF NOT EXISTS broker_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User ownership - CRITICAL for multi-user isolation
    user_id UUID NOT NULL,

    -- Broker identification
    broker_name VARCHAR(50) NOT NULL,
    account_name VARCHAR(100),

    -- Encrypted credentials (MUST be encrypted before storage)
    encrypted_api_key TEXT NOT NULL,
    encrypted_api_secret TEXT NOT NULL,
    encrypted_passphrase TEXT,

    -- Status flags
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_paper_trading BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,

    -- Broker-specific configuration (JSON)
    config JSONB,

    -- Connection metadata
    last_verified_at TIMESTAMP,
    verification_error TEXT,

    -- Audit fields
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Foreign key
    CONSTRAINT fk_broker_credential_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Unique constraint: One account per user per broker type
    CONSTRAINT uq_user_broker_account
    UNIQUE (user_id, broker_name, account_name)
);

-- Indexes for broker_credentials
CREATE INDEX IF NOT EXISTS idx_broker_cred_user_id ON broker_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_broker_cred_user_broker ON broker_credentials(user_id, broker_name);
CREATE INDEX IF NOT EXISTS idx_broker_cred_user_active ON broker_credentials(user_id, is_active);

COMMENT ON TABLE broker_credentials IS 'User-specific broker credentials (encrypted at rest)';
COMMENT ON COLUMN broker_credentials.user_id IS 'CRITICAL: User isolation - all queries MUST filter by this';
COMMENT ON COLUMN broker_credentials.encrypted_api_key IS 'SECURITY: Must be encrypted using Fernet encryption before storage';
COMMENT ON COLUMN broker_credentials.encrypted_api_secret IS 'SECURITY: Must be encrypted using Fernet encryption before storage';

-- ==============================================================================
-- 6. ADD broker_credential_id TO orders TABLE
-- ==============================================================================

-- Add broker_credential_id to track which broker account was used
ALTER TABLE orders
ADD COLUMN IF NOT EXISTS broker_credential_id UUID;

-- Add foreign key constraint
ALTER TABLE orders
ADD CONSTRAINT fk_order_broker_credential
FOREIGN KEY (broker_credential_id) REFERENCES broker_credentials(id) ON DELETE SET NULL;

-- Add index
CREATE INDEX IF NOT EXISTS idx_order_broker_credential ON orders(broker_credential_id);

COMMENT ON COLUMN orders.broker_credential_id IS 'Links order to specific broker account used for execution';

-- ==============================================================================
-- 7. CREATE TRIGGER FOR updated_at TIMESTAMPS
-- ==============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to trading_decisions
DROP TRIGGER IF EXISTS update_trading_decisions_updated_at ON trading_decisions;
CREATE TRIGGER update_trading_decisions_updated_at
BEFORE UPDATE ON trading_decisions
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to broker_credentials
DROP TRIGGER IF EXISTS update_broker_credentials_updated_at ON broker_credentials;
CREATE TRIGGER update_broker_credentials_updated_at
BEFORE UPDATE ON broker_credentials
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ==============================================================================
-- COMMIT TRANSACTION
-- ==============================================================================

COMMIT;

-- ==============================================================================
-- VERIFICATION QUERIES
-- ==============================================================================

-- Verify tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND column_name = 'user_id') as has_user_id
FROM
    information_schema.tables t
WHERE
    table_schema = 'public'
    AND table_name IN ('signals', 'trading_decisions', 'evidence', 'analysis_reports', 'broker_credentials', 'orders')
ORDER BY table_name;

-- Verify indexes exist
SELECT
    tablename,
    indexname
FROM
    pg_indexes
WHERE
    schemaname = 'public'
    AND (indexname LIKE '%user%' OR tablename IN ('signals', 'trading_decisions', 'evidence', 'analysis_reports', 'broker_credentials'))
ORDER BY tablename, indexname;

-- ==============================================================================
-- POST-MIGRATION NOTES
-- ==============================================================================

/*
IMPORTANT: After running this migration:

1. UPDATE EXISTING DATA:
   - Assign user_id to existing signals (or delete if not needed)
   - Set signals.user_id to NOT NULL after data migration

2. GENERATE ENCRYPTION KEY:
   - Run: python3 -m shared.utils.encryption
   - Save key to environment variable: ENCRYPTION_KEY=<generated-key>

3. UPDATE APPLICATION CODE:
   - All queries MUST filter by user_id
   - Use get_current_user dependency on all protected endpoints
   - Encrypt broker credentials before storage

4. TEST MULTI-TENANCY:
   - Create two test users
   - Verify User A cannot see User B's data
   - Test broker credential isolation

5. SECURITY REVIEW:
   - Verify Row-Level Security is enforced
   - Check all API endpoints require authentication
   - Audit log access to broker credentials
*/
