import { ApiClient, ApiResponse } from '../clients/apiClient';
import config from '../../config/config';

/**
 * Executor Service API Client
 *
 * Handles all executor service endpoints:
 * - Order execution
 * - Position sizing
 * - Risk checks
 * - Health checks
 *
 * Used for API and E2E tests.
 */

export interface ExecuteOrderRequest {
  user_id: string;
  symbol: string;
  asset_class: 'stock' | 'crypto' | 'forex';
  side: 'buy' | 'sell';
  order_type: 'market' | 'limit' | 'stop_loss' | 'stop_limit' | 'trailing_stop';
  quantity: number;
  limit_price?: number;
  stop_price?: number;
  stop_loss_price?: number;
  take_profit_price?: number;
}

export interface ExecuteOrderResponse {
  success: boolean;
  order_id?: number;
  broker_order_id?: string;
  symbol: string;
  side: string;
  quantity: number;
  status: string;
  filled_quantity?: number;
  avg_fill_price?: number;
  commission?: number;
  submitted_at?: string;
  filled_at?: string;
  error_message?: string;
}

export interface PositionSizeRequest {
  account_balance?: number;
  entry_price: number;
  stop_loss_price: number;
  risk_per_trade_percent?: number;
  method?: 'fixed_risk' | 'fixed_amount' | 'kelly';
  risk_multiplier?: number;
}

export interface PositionSizeResponse {
  success: boolean;
  quantity: number;
  position_value: number;
  risk_amount: number;
  risk_percent: number;
  account_balance: number;
  entry_price: number;
  stop_loss_price: number;
  stop_loss_distance: number;
  error_message?: string;
}

export interface RiskCheckRequest {
  user_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  quantity: number;
  entry_price: number;
  stop_loss_price?: number;
}

export interface RiskCheckResponse {
  approved: boolean;
  risk_score: number;
  position_risk_percent: number;
  total_account_risk_percent: number;
  margin_usage_percent: number;
  positions_count: number;
  max_positions_allowed: number;
  positions_in_symbol: number;
  violations: string[];
  warnings: string[];
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
  database_connected: boolean;
  alpaca_connected: boolean;
  binance_connected: boolean;
}

export class ExecutorService {
  private client: ApiClient;
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8007') {
    this.baseURL = baseURL;
    this.client = new ApiClient(baseURL);
  }

  /**
   * Initialize the service
   */
  async init(): Promise<void> {
    await this.client.init();
  }

  /**
   * Dispose of the service
   */
  async dispose(): Promise<void> {
    await this.client.dispose();
  }

  /**
   * Execute a trade order
   */
  async executeOrder(
    orderRequest: ExecuteOrderRequest
  ): Promise<ApiResponse<ExecuteOrderResponse>> {
    return await this.client.post<ExecuteOrderResponse>(
      '/api/v1/execute',
      orderRequest
    );
  }

  /**
   * Calculate optimal position size
   */
  async calculatePositionSize(
    request: PositionSizeRequest
  ): Promise<ApiResponse<PositionSizeResponse>> {
    return await this.client.post<PositionSizeResponse>(
      '/api/v1/position-size',
      request
    );
  }

  /**
   * Check risk before executing order
   */
  async checkRisk(
    request: RiskCheckRequest
  ): Promise<ApiResponse<RiskCheckResponse>> {
    return await this.client.post<RiskCheckResponse>(
      '/api/v1/risk-check',
      request
    );
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<ApiResponse<HealthResponse>> {
    return await this.client.get<HealthResponse>('/api/v1/health');
  }

  /**
   * Helper: Create test order request
   */
  createTestOrderRequest(overrides: Partial<ExecuteOrderRequest> = {}): ExecuteOrderRequest {
    const timestamp = Date.now();
    return {
      user_id: `test_user_${timestamp}`,
      symbol: 'AAPL',
      asset_class: 'stock',
      side: 'buy',
      order_type: 'market',
      quantity: 1,
      ...overrides,
    };
  }

  /**
   * Helper: Create test position size request
   */
  createTestPositionSizeRequest(
    overrides: Partial<PositionSizeRequest> = {}
  ): PositionSizeRequest {
    return {
      account_balance: 10000,
      entry_price: 150.0,
      stop_loss_price: 145.0,
      risk_per_trade_percent: 1.0,
      method: 'fixed_risk',
      risk_multiplier: 1.0,
      ...overrides,
    };
  }

  /**
   * Helper: Create test risk check request
   */
  createTestRiskCheckRequest(
    overrides: Partial<RiskCheckRequest> = {}
  ): RiskCheckRequest {
    const timestamp = Date.now();
    return {
      user_id: `test_user_${timestamp}`,
      symbol: 'AAPL',
      side: 'buy',
      quantity: 10,
      entry_price: 150.0,
      stop_loss_price: 145.0,
      ...overrides,
    };
  }
}
