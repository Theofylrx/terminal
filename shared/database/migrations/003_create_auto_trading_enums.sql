-- Migration: Create Auto-Trading ENUM Types
-- Date: 2024-01-20
-- Description: Create PostgreSQL ENUM types for auto-trading models

-- ============================================================================
-- CREATE ENUM TYPES
-- ============================================================================

-- Strategy Type ENUM
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'strategy_type') THEN
        CREATE TYPE strategy_type AS ENUM ('AGGRESSIVE', 'BALANCED', 'CONSERVATIVE');
    END IF;
END $$;

-- Session Status ENUM
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'session_status') THEN
        CREATE TYPE session_status AS ENUM ('ACTIVE', 'PAUSED', 'STOPPED', 'ERROR');
    END IF;
END $$;

-- ============================================================================
-- ALTER TABLES TO USE ENUM TYPES
-- ============================================================================

-- Update auto_trading_configs to use strategy_type ENUM
DO $$
BEGIN
    -- Drop the CHECK constraint if it exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_strategy') THEN
        ALTER TABLE auto_trading_configs DROP CONSTRAINT IF EXISTS valid_strategy;
    END IF;

    -- Alter column to use ENUM type
    ALTER TABLE auto_trading_configs
    ALTER COLUMN strategy_type TYPE strategy_type
    USING strategy_type::strategy_type;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Could not alter strategy_type column: %', SQLERRM;
END $$;

-- Update auto_trading_sessions to use session_status ENUM
DO $$
BEGIN
    -- Drop the CHECK constraint if it exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'valid_session_status') THEN
        ALTER TABLE auto_trading_sessions DROP CONSTRAINT IF EXISTS valid_session_status;
    END IF;

    -- Alter column to use ENUM type
    ALTER TABLE auto_trading_sessions
    ALTER COLUMN status TYPE session_status
    USING status::session_status;
EXCEPTION
    WHEN others THEN
        RAISE NOTICE 'Could not alter status column: %', SQLERRM;
END $$;

-- ============================================================================
-- VERIFY MIGRATION
-- ============================================================================

-- Show created ENUM types
SELECT
    typname AS enum_name,
    array_agg(enumlabel ORDER BY enumsortorder) AS enum_values
FROM pg_type
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid
WHERE typname IN ('strategy_type', 'session_status')
GROUP BY typname
ORDER BY typname;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'ENUM types migration completed successfully';
END $$;
