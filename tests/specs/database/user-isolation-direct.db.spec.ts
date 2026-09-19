import { test, expect } from '@playwright/test';
import { DatabaseClient } from '../../lib/database/clients/dbClient';
import crypto from 'crypto';

/**
 * Database User Isolation Tests (Direct DB Access)
 *
 * Tests critical multi-tenant security without API dependency:
 * - User data isolation
 * - Signal ownership
 * - Trading decision ownership
 * - Broker credential isolation
 * - CASCADE delete behavior
 *
 * Tags: @database @isolation @critical @standalone
 */

// Helper function to create a test user directly in the database
async function createTestUserDirect(db: DatabaseClient, prefix: string) {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000000);
  const userId = crypto.randomUUID();

  await db.query(
    `INSERT INTO users (id, email, username, hashed_password, is_active, is_verified)
     VALUES ($1, $2, $3, $4, $5, $6)`,
    [
      userId,
      `${prefix}_${timestamp}_${random}@test.com`,
      `${prefix}_${timestamp}_${random}`,
      'hashed_password_placeholder', // Not testing auth, just isolation
      true,
      false
    ]
  );

  return { id: userId, username: `${prefix}_${timestamp}_${random}` };
}

test.describe('User Data Isolation (Direct DB)', () => {
  let db: DatabaseClient;

  test.beforeAll(async () => {
    db = new DatabaseClient();
    await db.connect();
  });

  test.afterAll(async () => {
    await db.disconnect();
  });

  test('@database @isolation @critical @standalone - Signals are isolated per user', async () => {
    // Arrange - Create two test users directly
    const user1 = await createTestUserDirect(db, 'trader1');
    const user2 = await createTestUserDirect(db, 'trader2');

    // Create signal for user1
    await db.query(
      `INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [user1.id, 'BTCUSD', '1h', 'buy', 'active', 50000.0, 85.5]
    );

    // Create signal for user2
    await db.query(
      `INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [user2.id, 'ETHUSD', '1h', 'sell', 'active', 3000.0, 75.0]
    );

    // Act - Query signals for each user
    const user1Signals = await db.queryAll(
      'SELECT * FROM signals WHERE user_id = $1',
      [user1.id]
    );

    const user2Signals = await db.queryAll(
      'SELECT * FROM signals WHERE user_id = $1',
      [user2.id]
    );

    // Assert - Each user sees only their own signals
    expect(user1Signals.length).toBe(1);
    expect(user1Signals[0].symbol).toBe('BTCUSD');
    expect(user1Signals[0].user_id).toBe(user1.id);

    expect(user2Signals.length).toBe(1);
    expect(user2Signals[0].symbol).toBe('ETHUSD');
    expect(user2Signals[0].user_id).toBe(user2.id);

    // Verify no cross-contamination
    const user1CannotSeeUser2 = await db.queryAll(
      'SELECT * FROM signals WHERE user_id = $1 AND symbol = $2',
      [user1.id, 'ETHUSD']
    );
    expect(user1CannotSeeUser2.length).toBe(0);

    // Cleanup
    await db.cleanTestData(user1.id);
    await db.cleanTestData(user2.id);
    await db.query('DELETE FROM users WHERE id = $1 OR id = $2', [user1.id, user2.id]);
  });

  test('@database @isolation @critical @standalone - Trading decisions are isolated per user', async () => {
    // Arrange
    const user1 = await createTestUserDirect(db, 'trader1');
    const user2 = await createTestUserDirect(db, 'trader2');

    // Create trading decision for user1
    await db.query(
      `INSERT INTO trading_decisions (
        user_id, symbol, action, confidence, confidence_level, should_trade,
        primary_arguments, counter_arguments, risk_assessment,
        timeframe_summary, confidence_breakdown, executive_summary, detailed_reasoning
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
      [
        user1.id,
        'BTCUSD',
        'BUY',
        0.85,
        'HIGH',
        true,
        JSON.stringify([{ claim: 'Bullish setup', evidence: [] }]),
        JSON.stringify([]),
        JSON.stringify({ risk_level: 'LOW', primary_risks: [] }),
        JSON.stringify({ '1H': { bias: 'BULLISH' } }),
        JSON.stringify({ technical_confidence: 0.85 }),
        'Strong bullish setup',
        'Complete analysis...',
      ]
    );

    // Create trading decision for user2
    await db.query(
      `INSERT INTO trading_decisions (
        user_id, symbol, action, confidence, confidence_level, should_trade,
        primary_arguments, counter_arguments, risk_assessment,
        timeframe_summary, confidence_breakdown, executive_summary, detailed_reasoning
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
      [
        user2.id,
        'ETHUSD',
        'SELL',
        0.75,
        'MODERATE',
        true,
        JSON.stringify([{ claim: 'Bearish setup', evidence: [] }]),
        JSON.stringify([]),
        JSON.stringify({ risk_level: 'MODERATE', primary_risks: [] }),
        JSON.stringify({ '1H': { bias: 'BEARISH' } }),
        JSON.stringify({ technical_confidence: 0.75 }),
        'Bearish setup detected',
        'Complete analysis...',
      ]
    );

    // Act
    const user1Decisions = await db.queryAll(
      'SELECT * FROM trading_decisions WHERE user_id = $1',
      [user1.id]
    );

    const user2Decisions = await db.queryAll(
      'SELECT * FROM trading_decisions WHERE user_id = $1',
      [user2.id]
    );

    // Assert
    expect(user1Decisions.length).toBe(1);
    expect(user1Decisions[0].symbol).toBe('BTCUSD');
    expect(user1Decisions[0].action).toBe('BUY');

    expect(user2Decisions.length).toBe(1);
    expect(user2Decisions[0].symbol).toBe('ETHUSD');
    expect(user2Decisions[0].action).toBe('SELL');

    // Cleanup
    await db.cleanTestData(user1.id);
    await db.cleanTestData(user2.id);
    await db.query('DELETE FROM users WHERE id = $1 OR id = $2', [user1.id, user2.id]);
  });

  test('@database @isolation @critical @standalone - Broker credentials are isolated per user', async () => {
    // Arrange
    const user1 = await createTestUserDirect(db, 'trader1');
    const user2 = await createTestUserDirect(db, 'trader2');

    // Create broker credential for user1 (Alpaca)
    await db.query(
      `INSERT INTO broker_credentials (
        user_id, broker_name, account_name,
        encrypted_api_key, encrypted_api_secret, is_paper_trading
      )
      VALUES ($1, $2, $3, $4, $5, $6)`,
      [user1.id, 'alpaca', 'Alpaca Account', 'encrypted_key_1', 'encrypted_secret_1', true]
    );

    // Create broker credential for user2 (Binance)
    await db.query(
      `INSERT INTO broker_credentials (
        user_id, broker_name, account_name,
        encrypted_api_key, encrypted_api_secret, is_paper_trading
      )
      VALUES ($1, $2, $3, $4, $5, $6)`,
      [user2.id, 'binance', 'Binance Account', 'encrypted_key_2', 'encrypted_secret_2', true]
    );

    // Act
    const user1Brokers = await db.queryAll(
      'SELECT * FROM broker_credentials WHERE user_id = $1',
      [user1.id]
    );

    const user2Brokers = await db.queryAll(
      'SELECT * FROM broker_credentials WHERE user_id = $1',
      [user2.id]
    );

    // Assert
    expect(user1Brokers.length).toBe(1);
    expect(user1Brokers[0].broker_name).toBe('alpaca');
    expect(user1Brokers[0].encrypted_api_key).toBe('encrypted_key_1');

    expect(user2Brokers.length).toBe(1);
    expect(user2Brokers[0].broker_name).toBe('binance');
    expect(user2Brokers[0].encrypted_api_key).toBe('encrypted_key_2');

    // Verify isolation: User1 cannot see User2's broker
    const crossContamination = await db.queryAll(
      'SELECT * FROM broker_credentials WHERE user_id = $1 AND broker_name = $2',
      [user1.id, 'binance']
    );
    expect(crossContamination.length).toBe(0);

    // Cleanup
    await db.cleanTestData(user1.id);
    await db.cleanTestData(user2.id);
    await db.query('DELETE FROM users WHERE id = $1 OR id = $2', [user1.id, user2.id]);
  });

  test('@database @isolation @critical @standalone - CASCADE delete removes all user data', async () => {
    // Arrange
    const user = await createTestUserDirect(db, 'trader_cascade');

    // Create related data
    await db.query(
      'INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [user.id, 'BTCUSD', '1h', 'buy', 'active', 50000.0, 85.5]
    );

    await db.query(
      'INSERT INTO broker_credentials (user_id, broker_name, encrypted_api_key, encrypted_api_secret, is_paper_trading) VALUES ($1, $2, $3, $4, $5)',
      [user.id, 'alpaca', 'key', 'secret', true]
    );

    // Verify data exists
    const signalsBefore = await db.count('signals', { user_id: user.id });
    const brokersBefore = await db.count('broker_credentials', { user_id: user.id });

    expect(signalsBefore).toBeGreaterThan(0);
    expect(brokersBefore).toBeGreaterThan(0);

    // Act - Delete user (should cascade)
    await db.query('DELETE FROM users WHERE id = $1', [user.id]);

    // Assert - All related data deleted
    const signalsAfter = await db.count('signals', { user_id: user.id });
    const brokersAfter = await db.count('broker_credentials', { user_id: user.id });

    expect(signalsAfter).toBe(0);
    expect(brokersAfter).toBe(0);
  });

  test('@database @models @standalone - User indexes exist for performance', async () => {
    // Query to check if user_id indexes exist
    const indexes = await db.queryAll(`
      SELECT
        tablename,
        indexname
      FROM
        pg_indexes
      WHERE
        schemaname = 'public'
        AND indexname LIKE '%user_id%'
      ORDER BY tablename
    `);

    // Assert - Critical tables have user_id indexes
    const indexedTables = indexes.map((idx: any) => idx.tablename);

    expect(indexedTables).toContain('signals');
    expect(indexedTables).toContain('trading_decisions');
    expect(indexedTables).toContain('broker_credentials');

    // Verify specific indexes exist
    const indexNames = indexes.map((idx: any) => idx.indexname);
    expect(indexNames).toContain('idx_signal_user_id');
    expect(indexNames).toContain('idx_trading_decision_user_id');
    expect(indexNames).toContain('idx_broker_cred_user_id');
  });

  test('@database @isolation @critical @standalone - No data leakage between users', async () => {
    // Arrange - Create 3 users with different data
    const user1 = await createTestUserDirect(db, 'trader1');
    const user2 = await createTestUserDirect(db, 'trader2');
    const user3 = await createTestUserDirect(db, 'trader3');

    // Each user gets their own signal
    await db.query(
      'INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [user1.id, 'BTCUSD', '1h', 'buy', 'active', 50000.0, 85.5]
    );
    await db.query(
      'INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [user2.id, 'ETHUSD', '1h', 'sell', 'active', 3000.0, 75.0]
    );
    await db.query(
      'INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [user3.id, 'AAPL', '1h', 'buy', 'active', 180.0, 90.0]
    );

    // Act - Query each user's signals
    const user1Count = await db.count('signals', { user_id: user1.id });
    const user2Count = await db.count('signals', { user_id: user2.id });
    const user3Count = await db.count('signals', { user_id: user3.id });

    // Assert - Each user has exactly 1 signal
    expect(user1Count).toBe(1);
    expect(user2Count).toBe(1);
    expect(user3Count).toBe(1);

    // Verify total signals in database
    const totalCount = await db.count('signals');
    expect(totalCount).toBeGreaterThanOrEqual(3);

    // Verify user1 cannot see other users' signals
    const user1Signals = await db.queryAll('SELECT * FROM signals WHERE user_id = $1', [user1.id]);
    expect(user1Signals.every((s: any) => s.user_id === user1.id)).toBeTruthy();
    expect(user1Signals.every((s: any) => s.symbol === 'BTCUSD')).toBeTruthy();

    // Cleanup
    await db.cleanTestData(user1.id);
    await db.cleanTestData(user2.id);
    await db.cleanTestData(user3.id);
    await db.query('DELETE FROM users WHERE id IN ($1, $2, $3)', [user1.id, user2.id, user3.id]);
  });
});
