import { Pool, PoolClient, QueryResult } from 'pg';
import config from '../../config/config';

/**
 * Database Client for Terminal Trading System
 *
 * Provides methods for:
 * - Connection management
 * - Query execution
 * - Transaction handling
 * - Data cleanup
 */
export class DatabaseClient {
  private pool: Pool | null = null;
  private client: PoolClient | null = null;
  private isConnected: boolean = false;

  /**
   * Connect to database
   */
  async connect(): Promise<void> {
    if (this.isConnected) {
      console.log('Database already connected');
      return;
    }

    this.pool = new Pool({
      host: config.database.host,
      port: config.database.port,
      database: config.database.database,
      user: config.database.user,
      password: config.database.password,
      ssl: config.database.ssl ? { rejectUnauthorized: false } : false,
      max: 10, // Maximum number of clients in pool
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: config.timeouts.dbQuery,
    });

    // Test connection
    this.client = await this.pool.connect();
    await this.client.query('SELECT NOW()');
    this.client.release();
    this.client = null;

    this.isConnected = true;
    console.log('✅ Database connected successfully');
  }

  /**
   * Disconnect from database
   */
  async disconnect(): Promise<void> {
    if (this.client) {
      this.client.release();
      this.client = null;
    }

    if (this.pool) {
      await this.pool.end();
      this.pool = null;
    }

    this.isConnected = false;
    console.log('Database disconnected');
  }

  /**
   * Execute a query
   */
  async query<T = any>(
    text: string,
    params?: any[]
  ): Promise<QueryResult<T>> {
    this.ensureConnected();

    try {
      const result = await this.pool!.query<T>(text, params);
      return result;
    } catch (error) {
      console.error('Query error:', error);
      console.error('Query:', text);
      console.error('Params:', params);
      throw error;
    }
  }

  /**
   * Execute a query and return first row
   */
  async queryOne<T = any>(
    text: string,
    params?: any[]
  ): Promise<T | null> {
    const result = await this.query<T>(text, params);
    return result.rows[0] || null;
  }

  /**
   * Execute a query and return all rows
   */
  async queryAll<T = any>(
    text: string,
    params?: any[]
  ): Promise<T[]> {
    const result = await this.query<T>(text, params);
    return result.rows;
  }

  /**
   * Begin transaction
   */
  async beginTransaction(): Promise<void> {
    await this.query('BEGIN');
  }

  /**
   * Commit transaction
   */
  async commitTransaction(): Promise<void> {
    await this.query('COMMIT');
  }

  /**
   * Rollback transaction
   */
  async rollbackTransaction(): Promise<void> {
    await this.query('ROLLBACK');
  }

  /**
   * Execute within transaction
   */
  async transaction<T>(
    callback: (client: DatabaseClient) => Promise<T>
  ): Promise<T> {
    await this.beginTransaction();

    try {
      const result = await callback(this);
      await this.commitTransaction();
      return result;
    } catch (error) {
      await this.rollbackTransaction();
      throw error;
    }
  }

  /**
   * Insert record
   */
  async insert(
    table: string,
    data: Record<string, any>
  ): Promise<QueryResult> {
    const keys = Object.keys(data);
    const values = Object.values(data);
    const placeholders = keys.map((_, i) => `$${i + 1}`).join(', ');

    const query = `
      INSERT INTO ${table} (${keys.join(', ')})
      VALUES (${placeholders})
      RETURNING *
    `;

    return await this.query(query, values);
  }

  /**
   * Update record
   */
  async update(
    table: string,
    data: Record<string, any>,
    where: Record<string, any>
  ): Promise<QueryResult> {
    const setKeys = Object.keys(data);
    const setValues = Object.values(data);
    const whereKeys = Object.keys(where);
    const whereValues = Object.values(where);

    const setClause = setKeys
      .map((key, i) => `${key} = $${i + 1}`)
      .join(', ');

    const whereClause = whereKeys
      .map((key, i) => `${key} = $${setKeys.length + i + 1}`)
      .join(' AND ');

    const query = `
      UPDATE ${table}
      SET ${setClause}
      WHERE ${whereClause}
      RETURNING *
    `;

    return await this.query(query, [...setValues, ...whereValues]);
  }

  /**
   * Delete record
   */
  async delete(
    table: string,
    where: Record<string, any>
  ): Promise<QueryResult> {
    const keys = Object.keys(where);
    const values = Object.values(where);

    const whereClause = keys
      .map((key, i) => `${key} = $${i + 1}`)
      .join(' AND ');

    const query = `
      DELETE FROM ${table}
      WHERE ${whereClause}
      RETURNING *
    `;

    return await this.query(query, values);
  }

  /**
   * Truncate table
   */
  async truncate(table: string, cascade: boolean = false): Promise<void> {
    const cascadeClause = cascade ? 'CASCADE' : '';
    await this.query(`TRUNCATE TABLE ${table} ${cascadeClause}`);
  }

  /**
   * Check if record exists
   */
  async exists(
    table: string,
    where: Record<string, any>
  ): Promise<boolean> {
    const keys = Object.keys(where);
    const values = Object.values(where);

    const whereClause = keys
      .map((key, i) => `${key} = $${i + 1}`)
      .join(' AND ');

    const query = `
      SELECT EXISTS(
        SELECT 1 FROM ${table}
        WHERE ${whereClause}
      ) as exists
    `;

    const result = await this.queryOne<{ exists: boolean }>(query, values);
    return result?.exists || false;
  }

  /**
   * Count records
   */
  async count(
    table: string,
    where?: Record<string, any>
  ): Promise<number> {
    let query = `SELECT COUNT(*) as count FROM ${table}`;
    let values: any[] = [];

    if (where) {
      const keys = Object.keys(where);
      values = Object.values(where);

      const whereClause = keys
        .map((key, i) => `${key} = $${i + 1}`)
        .join(' AND ');

      query += ` WHERE ${whereClause}`;
    }

    const result = await this.queryOne<{ count: string }>(query, values);
    return parseInt(result?.count || '0', 10);
  }

  /**
   * Clean test data (delete all records from test user)
   */
  async cleanTestData(userId: string): Promise<void> {
    const tables = [
      'signals',
      'trading_decisions',
      'evidence',
      'analysis_reports',
      'broker_credentials',
      'orders',
      'positions',
    ];

    for (const table of tables) {
      await this.query(`DELETE FROM ${table} WHERE user_id = $1`, [userId]);
    }

    console.log(`✅ Cleaned test data for user: ${userId}`);
  }

  /**
   * Reset database to clean state
   */
  async resetDatabase(): Promise<void> {
    console.log('⚠️  Resetting database to clean state...');

    // Delete all test users (this will cascade delete all related data)
    await this.query(`
      DELETE FROM users
      WHERE email LIKE '%@terminal.test'
      OR username LIKE '%_test'
    `);

    console.log('✅ Database reset complete');
  }

  /**
   * Get table row count
   */
  async getTableRowCount(table: string): Promise<number> {
    const result = await this.queryOne<{ count: string }>(
      `SELECT COUNT(*) as count FROM ${table}`
    );
    return parseInt(result?.count || '0', 10);
  }

  /**
   * Verify database connection
   */
  async verifyConnection(): Promise<boolean> {
    try {
      await this.query('SELECT 1');
      return true;
    } catch (error) {
      console.error('Database connection verification failed:', error);
      return false;
    }
  }

  /**
   * Ensure connected before executing queries
   */
  private ensureConnected(): void {
    if (!this.isConnected || !this.pool) {
      throw new Error('Database not connected. Call connect() first.');
    }
  }

  /**
   * Get pool statistics
   */
  getPoolStats(): {
    totalCount: number;
    idleCount: number;
    waitingCount: number;
  } {
    if (!this.pool) {
      return { totalCount: 0, idleCount: 0, waitingCount: 0 };
    }

    return {
      totalCount: this.pool.totalCount,
      idleCount: this.pool.idleCount,
      waitingCount: this.pool.waitingCount,
    };
  }
}

// Export singleton instance
export const db = new DatabaseClient();
