-- Migration: Optimize OHLCV table for time-series queries
-- Date: 2026-09-20
-- Description: Add indexes for efficient time-range queries on OHLCV data

-- Note: TimescaleDB is not installed, so we'll use standard PostgreSQL indexes
-- If TimescaleDB is added later, this table can be converted to a hypertable

-- Add composite index for symbol + timeframe + timestamp queries
-- This is the most common query pattern for technical analysis
CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_timeframe_timestamp
ON ohlcv (symbol, timeframe, timestamp DESC);

-- Add index for timestamp-only queries (for latest data across all symbols)
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp
ON ohlcv (timestamp DESC);

-- Add index for volume-based queries (useful for liquidity analysis)
CREATE INDEX IF NOT EXISTS idx_ohlcv_volume
ON ohlcv (volume DESC) WHERE volume > 0;

-- Add partial index for recent data (last 30 days) for faster queries
CREATE INDEX IF NOT EXISTS idx_ohlcv_recent
ON ohlcv (symbol, timeframe, timestamp DESC)
WHERE timestamp > NOW() - INTERVAL '30 days';

-- Create index on trade_count for institutional activity detection
CREATE INDEX IF NOT EXISTS idx_ohlcv_trade_count
ON ohlcv (trade_count DESC) WHERE trade_count IS NOT NULL;

-- Analyze table to update statistics for query planner
ANALYZE ohlcv;

-- Show index information
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'ohlcv'
ORDER BY indexname;
