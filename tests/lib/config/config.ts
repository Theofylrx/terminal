import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

/**
 * Configuration for Terminal Trading System Tests
 *
 * Supports multiple environments:
 * - local: Local development
 * - staging: Staging environment
 * - production: Production environment (read-only tests)
 */

export interface TerminalConfig {
  // Environment
  environment: string;

  // Frontend URLs
  frontendUrl: string;

  // API URLs
  apiBaseUrl: string;
  authServiceUrl: string;
  tradingServiceUrl: string;
  technicalAnalystServiceUrl: string;
  marketDataServiceUrl: string;

  // Database connection
  database: {
    host: string;
    port: number;
    database: string;
    user: string;
    password: string;
    ssl: boolean;
  };

  // Test users
  testUsers: {
    admin: {
      username: string;
      email: string;
      password: string;
    };
    trader1: {
      username: string;
      email: string;
      password: string;
    };
    trader2: {
      username: string;
      email: string;
      password: string;
    };
  };

  // Test data
  testSymbols: string[];

  // Broker credentials (for testing)
  brokers: {
    alpaca: {
      apiKey: string;
      apiSecret: string;
      baseUrl: string;
    };
    binance: {
      apiKey: string;
      apiSecret: string;
      baseUrl: string;
    };
  };

  // Timeouts
  timeouts: {
    short: number;
    medium: number;
    long: number;
    apiRequest: number;
    dbQuery: number;
  };
}

const environment = process.env.ENVIRONMENT || 'local';

const config: TerminalConfig = {
  environment,

  // Frontend URLs
  frontendUrl: process.env.FRONTEND_URL || 'http://localhost:3000',

  // API URLs
  apiBaseUrl: process.env.API_BASE_URL || 'http://localhost:8000',
  authServiceUrl: process.env.AUTH_SERVICE_URL || 'http://localhost:8001',
  tradingServiceUrl: process.env.TRADING_SERVICE_URL || 'http://localhost:8002',
  technicalAnalystServiceUrl: process.env.TECHNICAL_ANALYST_SERVICE_URL || 'http://localhost:8000',
  marketDataServiceUrl: process.env.MARKET_DATA_SERVICE_URL || 'http://localhost:8003',

  // Database connection
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME || 'terminal',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',
    ssl: process.env.DB_SSL === 'true',
  },

  // Test users
  testUsers: {
    admin: {
      username: process.env.TEST_ADMIN_USERNAME || 'admin_test',
      email: process.env.TEST_ADMIN_EMAIL || 'admin@terminal.test',
      password: process.env.TEST_ADMIN_PASSWORD || 'Admin123!',
    },
    trader1: {
      username: process.env.TEST_TRADER1_USERNAME || 'trader1_test',
      email: process.env.TEST_TRADER1_EMAIL || 'trader1@terminal.test',
      password: process.env.TEST_TRADER1_PASSWORD || 'Trader1Pass123!',
    },
    trader2: {
      username: process.env.TEST_TRADER2_USERNAME || 'trader2_test',
      email: process.env.TEST_TRADER2_EMAIL || 'trader2@terminal.test',
      password: process.env.TEST_TRADER2_PASSWORD || 'Trader2Pass123!',
    },
  },

  // Test symbols
  testSymbols: ['BTCUSD', 'ETHUSD', 'AAPL', 'TSLA'],

  // Broker credentials (for testing - use paper trading accounts)
  brokers: {
    alpaca: {
      apiKey: process.env.TEST_ALPACA_API_KEY || '',
      apiSecret: process.env.TEST_ALPACA_API_SECRET || '',
      baseUrl: process.env.TEST_ALPACA_BASE_URL || 'https://paper-api.alpaca.markets',
    },
    binance: {
      apiKey: process.env.TEST_BINANCE_API_KEY || '',
      apiSecret: process.env.TEST_BINANCE_API_SECRET || '',
      baseUrl: process.env.TEST_BINANCE_BASE_URL || 'https://testnet.binance.vision',
    },
  },

  // Timeouts (in milliseconds)
  timeouts: {
    short: 5000,      // 5 seconds
    medium: 15000,    // 15 seconds
    long: 30000,      // 30 seconds
    apiRequest: 10000, // 10 seconds
    dbQuery: 5000,    // 5 seconds
  },
};

export default config;
