import { test, expect } from '@playwright/test';
import { DatabaseClient } from '../../lib/database/clients/dbClient';
import { AuthService } from '../../lib/api/services/authService';

/**
 * Database User Isolation Tests
 *
 * Tests critical multi-tenant security:
 * - User data isolation
 * - Signal ownership
 * - Trading decision ownership
 * - Broker credential isolation
 *
 * Tags: @database @isolation @critical
 */

test.describe('User Data Isolation', () => {
  let db: DatabaseClient;
  let authService: AuthService;

  test.beforeAll(async () => {
    db = new DatabaseClient();
    await db.connect();

    authService = new AuthService();
    await authService.init();
  });

  test.afterAll(async () => {
    await db.disconnect();
    await authService.dispose();
  });

  test('@database @isolation @critical - Signals are isolated per user', async () => {
    // Arrange - Create two test users
    const user1 = await authService.createTestUser('trader1');
    const user2 = await authService.createTestUser('trader2');

    // Create signal for user1
    await db.query(
      `INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [user1.user.id, 'BTCUSD', '1h', 'buy', 'active', 50000.0, 85.5]
    );

    // Create signal for user2
    await db.query(
      `INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [user2.user.id, 'ETHUSD', '1h', 'sell', 'active', 3000.0, 75.0]
    );

    // Act - Query signals for user1
    const user1Signals = await db.queryAll(
      'SELECT * FROM signals WHERE user_id = $1',
      [user1.user.id]
    );

    const user2Signals = await db.queryAll(
      'SELECT * FROM signals WHERE user_id = $1',
      [user2.user.id]
    );

    // Assert - Each user sees only their own signals
    expect(user1Signals.length).toBe(1);
    expect(user1Signals[0].symbol).toBe('BTCUSD');
    expect(user1Signals[0].user_id).toBe(user1.user.id);

    expect(user2Signals.length).toBe(1);
    expect(user2Signals[0].symbol).toBe('ETHUSD');
    expect(user2Signals[0].user_id).toBe(user2.user.id);

    // Cleanup
    await db.cleanTestData(user1.user.id);
    await db.cleanTestData(user2.user.id);
  });

  test('@database @isolation @critical - Trading decisions are isolated per user', async () => {
    // Arrange
    const user1 = await authService.createTestUser('trader1');
    const user2 = await authService.createTestUser('trader2');

    // Create trading decision for user1
    await db.query(
      `INSERT INTO trading_decisions (
        user_id, symbol, action, confidence, confidence_level, should_trade,
        primary_arguments, counter_arguments, risk_assessment,
        timeframe_summary, confidence_breakdown, executive_summary, detailed_reasoning
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
      [
        user1.user.id,
        'BTCUSD',
        'BUY',
        0.85,
        'HIGH',
        'true',
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
        user2.user.id,
        'ETHUSD',
        'SELL',
        0.75,
        'MODERATE',
        'true',
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
      [user1.user.id]
    );

    const user2Decisions = await db.queryAll(
      'SELECT * FROM trading_decisions WHERE user_id = $1',
      [user2.user.id]
    );

    // Assert
    expect(user1Decisions.length).toBe(1);
    expect(user1Decisions[0].symbol).toBe('BTCUSD');
    expect(user1Decisions[0].action).toBe('BUY');

    expect(user2Decisions.length).toBe(1);
    expect(user2Decisions[0].symbol).toBe('ETHUSD');
    expect(user2Decisions[0].action).toBe('SELL');

    // Cleanup
    await db.cleanTestData(user1.user.id);
    await db.cleanTestData(user2.user.id);
  });

  test('@database @isolation @critical - Broker credentials are isolated per user', async () => {
    // Arrange
    const user1 = await authService.createTestUser('trader1');
    const user2 = await authService.createTestUser('trader2');

    // Create broker credential for user1 (Alpaca)
    await db.query(
      `INSERT INTO broker_credentials (
        user_id, broker_name, account_name,
        encrypted_api_key, encrypted_api_secret, is_paper_trading
      )
      VALUES ($1, $2, $3, $4, $5, $6)`,
      [user1.user.id, 'alpaca', 'Alpaca Account', 'encrypted_key_1', 'encrypted_secret_1', true]
    );

    // Create broker credential for user2 (Binance)
    await db.query(
      `INSERT INTO broker_credentials (
        user_id, broker_name, account_name,
        encrypted_api_key, encrypted_api_secret, is_paper_trading
      )
      VALUES ($1, $2, $3, $4, $5, $6)`,
      [user2.user.id, 'binance', 'Binance Account', 'encrypted_key_2', 'encrypted_secret_2', true]
    );

    // Act
    const user1Brokers = await db.queryAll(
      'SELECT * FROM broker_credentials WHERE user_id = $1',
      [user1.user.id]
    );

    const user2Brokers = await db.queryAll(
      'SELECT * FROM broker_credentials WHERE user_id = $1',
      [user2.user.id]
    );

    // Assert
    expect(user1Brokers.length).toBe(1);
    expect(user1Brokers[0].broker_name).toBe('alpaca');
    expect(user1Brokers[0].encrypted_api_key).toBe('encrypted_key_1');

    expect(user2Brokers.length).toBe(1);
    expect(user2Brokers[0].broker_name).toBe('binance');
    expect(user2Brokers[0].encrypted_api_key).toBe('encrypted_key_2');

    // Cleanup
    await db.cleanTestData(user1.user.id);
    await db.cleanTestData(user2.user.id);
  });

  test('@database @isolation @critical - CASCADE delete removes all user data', async () => {
    // Arrange
    const user = await authService.createTestUser('trader_cascade');

    // Create related data
    await db.query(
      'INSERT INTO signals (user_id, symbol, timeframe, signal_type, status, entry_price, confidence) VALUES ($1, $2, $3, $4, $5, $6, $7)',
      [user.user.id, 'BTCUSD', '1h', 'buy', 'active', 50000.0, 85.5]
    );

    await db.query(
      'INSERT INTO broker_credentials (user_id, broker_name, encrypted_api_key, encrypted_api_secret, is_paper_trading) VALUES ($1, $2, $3, $4, $5)',
      [user.user.id, 'alpaca', 'key', 'secret', true]
    );

    // Verify data exists
    const signalsBefore = await db.count('signals', { user_id: user.user.id });
    const brokersBefore = await db.count('broker_credentials', { user_id: user.user.id });

    expect(signalsBefore).toBeGreaterThan(0);
    expect(brokersBefore).toBeGreaterThan(0);

    // Act - Delete user (should cascade)
    await db.query('DELETE FROM users WHERE id = $1', [user.user.id]);

    // Assert - All related data deleted
    const signalsAfter = await db.count('signals', { user_id: user.user.id });
    const brokersAfter = await db.count('broker_credentials', { user_id: user.user.id });

    expect(signalsAfter).toBe(0);
    expect(brokersAfter).toBe(0);
  });

  test('@database @models - User indexes exist for performance', async () => {
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
  });
});
