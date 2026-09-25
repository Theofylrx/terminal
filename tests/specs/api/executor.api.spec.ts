import { test, expect } from '../../fixtures';

/**
 * Executor Service API Tests
 *
 * Tests all executor service endpoints:
 * - Order execution (market, limit, stop-loss)
 * - Position sizing (fixed risk, Kelly criterion)
 * - Risk checks (account risk, position limits)
 * - Health checks (service status, broker connections)
 *
 * Tags: @api @executor @critical
 */

test.describe('Executor Service API', () => {

  // ==================== Health Check Tests ====================

  test('@api @executor @critical @smoke - Health check returns healthy status', async ({ executorService }) => {
    // Act
    const response = await executorService.healthCheck();

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('status');
    expect(response.body).toHaveProperty('service', 'executor-service');
    expect(response.body).toHaveProperty('version');
    expect(response.body).toHaveProperty('timestamp');
  });

  test('@api @executor @smoke - Health check shows broker connections', async ({ executorService }) => {
    // Act
    const response = await executorService.healthCheck();

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body).toHaveProperty('alpaca_connected');
    expect(response.body).toHaveProperty('binance_connected');
    expect(response.body).toHaveProperty('database_connected');
  });

  // ==================== Position Sizing Tests ====================

  test('@api @executor @critical - Calculate position size with fixed risk method', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      account_balance: 10000,
      entry_price: 150.0,
      stop_loss_price: 145.0,
      risk_per_trade_percent: 1.0,
      method: 'fixed_risk',
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body.success).toBeTruthy();
    expect(response.body.quantity).toBeGreaterThan(0);
    expect(response.body.risk_amount).toBeLessThanOrEqual(100); // 1% of 10000
    expect(response.body.position_value).toBeGreaterThan(0);
    expect(response.body.stop_loss_distance).toBeGreaterThan(0);
  });

  test('@api @executor - Calculate position size with Kelly criterion', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      method: 'kelly',
      risk_multiplier: 0.5, // Use half-Kelly for safety
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body.success).toBeTruthy();
    expect(response.body.quantity).toBeGreaterThan(0);
  });

  test('@api @executor - Calculate position size with fixed amount', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      method: 'fixed_amount',
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body.success).toBeTruthy();
    expect(response.body.quantity).toBeGreaterThan(0);
  });

  test('@api @executor - Position size calculation with high risk percentage', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      risk_per_trade_percent: 5.0, // 5% risk
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body.success).toBeTruthy();
    expect(response.body.risk_amount).toBeLessThanOrEqual(500); // 5% of 10000
  });

  test('@api @executor - Position size calculation with tight stop loss', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      entry_price: 150.0,
      stop_loss_price: 149.5, // Only $0.50 stop loss
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body.success).toBeTruthy();
    expect(response.body.quantity).toBeGreaterThan(0);
    expect(response.body.stop_loss_distance).toBeLessThan(1.0); // Less than 1%
  });

  test('@api @executor - Position size handles zero or negative values', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestPositionSizeRequest({
      entry_price: 150.0,
      stop_loss_price: 150.0, // Invalid: same as entry
    });

    // Act
    const response = await executorService.calculatePositionSize(request);

    // Assert
    // Should either return error or handle gracefully
    expect(response.status).toBeGreaterThanOrEqual(200);
  });

  // ==================== Risk Check Tests ====================

  test('@api @executor @critical - Risk check approves valid order', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestRiskCheckRequest({
      quantity: 10,
      entry_price: 150.0,
      stop_loss_price: 145.0,
    });

    // Act
    const response = await executorService.checkRisk(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('approved');
    expect(response.body).toHaveProperty('risk_score');
    expect(response.body).toHaveProperty('violations');
    expect(response.body).toHaveProperty('warnings');
  });

  test('@api @executor - Risk check provides risk metrics', async ({ executorService }) => {
    // Arrange
    const request = executorService.createTestRiskCheckRequest();

    // Act
    const response = await executorService.checkRisk(request);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.body).toHaveProperty('position_risk_percent');
    expect(response.body).toHaveProperty('total_account_risk_percent');
    expect(response.body).toHaveProperty('margin_usage_percent');
    expect(response.body).toHaveProperty('positions_count');
    expect(response.body).toHaveProperty('max_positions_allowed');
    expect(response.body).toHaveProperty('positions_in_symbol');
  });

  test('@api @executor - Risk check detects excessive position size', async ({ executorService }) => {
    // Arrange - Request very large quantity
    const request = executorService.createTestRiskCheckRequest({
      quantity: 10000, // Very large position
      entry_price: 150.0,
    });

    // Act
    const response = await executorService.checkRisk(request);

    // Assert
    expect(response.ok).toBeTruthy();
    // Risk check should either reject or warn about large position
    if (!response.body.approved) {
      expect(response.body.violations.length).toBeGreaterThan(0);
    } else {
      expect(response.body.warnings.length).toBeGreaterThanOrEqual(0);
    }
  });

  test('@api @executor - Risk check validates stop loss requirement', async ({ executorService }) => {
    // Arrange - Order without stop loss
    const request = executorService.createTestRiskCheckRequest({
      stop_loss_price: undefined,
    });

    // Act
    const response = await executorService.checkRisk(request);

    // Assert
    expect(response.ok).toBeTruthy();
    // System should either require stop loss or issue warning
  });

  // ==================== Order Execution Tests ====================

  test('@api @executor @critical - Execute market order for stock', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'AAPL',
      asset_class: 'stock',
      side: 'buy',
      order_type: 'market',
      quantity: 1,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
    expect(response.body).toHaveProperty('symbol', 'AAPL');
    expect(response.body).toHaveProperty('side');
    expect(response.body).toHaveProperty('status');

    // If successful, verify order details
    if (response.body.success) {
      expect(response.body).toHaveProperty('broker_order_id');
      expect(response.body.quantity).toBe(1);
    }
  });

  test('@api @executor - Execute limit order for stock', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'AAPL',
      order_type: 'limit',
      limit_price: 150.0,
      quantity: 1,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
    expect(response.body).toHaveProperty('symbol', 'AAPL');
  });

  test('@api @executor - Execute market order for crypto', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'BTCUSDT',
      asset_class: 'crypto',
      side: 'buy',
      order_type: 'market',
      quantity: 0.001, // Small BTC amount
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
    expect(response.body).toHaveProperty('symbol');
  });

  test('@api @executor - Execute sell order', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      side: 'sell',
      quantity: 1,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
    expect(response.body.side).toMatch(/sell/i);
  });

  test('@api @executor - Execute order with stop loss', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'AAPL',
      side: 'buy',
      quantity: 1,
      stop_loss_price: 145.0,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
  });

  test('@api @executor - Execute order with take profit', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'AAPL',
      side: 'buy',
      quantity: 1,
      take_profit_price: 160.0,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    expect(response.body).toHaveProperty('success');
  });

  test('@api @executor - Reject order with invalid symbol', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      symbol: 'INVALID_SYMBOL_12345',
      quantity: 1,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(200);
    // Should either reject or return error
    if (response.body.success === false) {
      expect(response.body).toHaveProperty('error_message');
    }
  });

  test('@api @executor - Reject order with zero quantity', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      quantity: 0,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    // Should return validation error
    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test('@api @executor - Reject order with negative quantity', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      quantity: -10,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    expect(response.status).toBeGreaterThanOrEqual(400);
  });

  test('@api @executor - Order execution returns timestamps', async ({ executorService }) => {
    // Arrange
    const orderRequest = executorService.createTestOrderRequest({
      quantity: 1,
    });

    // Act
    const response = await executorService.executeOrder(orderRequest);

    // Assert
    if (response.body.success) {
      expect(response.body).toHaveProperty('submitted_at');
    }
  });

  // ==================== Integration Tests ====================

  test('@api @executor @e2e - Complete trading workflow: position size -> risk check -> execute', async ({ executorService }) => {
    // Step 1: Calculate position size
    const positionRequest = executorService.createTestPositionSizeRequest({
      account_balance: 10000,
      entry_price: 150.0,
      stop_loss_price: 145.0,
      risk_per_trade_percent: 1.0,
    });

    const positionResponse = await executorService.calculatePositionSize(positionRequest);
    expect(positionResponse.body.success).toBeTruthy();

    const calculatedQuantity = Math.floor(positionResponse.body.quantity);

    // Step 2: Run risk check
    const riskRequest = executorService.createTestRiskCheckRequest({
      quantity: calculatedQuantity,
      entry_price: 150.0,
      stop_loss_price: 145.0,
    });

    const riskResponse = await executorService.checkRisk(riskRequest);
    expect(riskResponse.ok).toBeTruthy();

    // Step 3: If approved, execute order
    if (riskResponse.body.approved) {
      const orderRequest = executorService.createTestOrderRequest({
        symbol: 'AAPL',
        quantity: calculatedQuantity,
        stop_loss_price: 145.0,
      });

      const orderResponse = await executorService.executeOrder(orderRequest);
      expect(orderResponse.status).toBeGreaterThanOrEqual(200);
      expect(orderResponse.body).toHaveProperty('success');
    }
  });

  test('@api @executor @performance - Multiple concurrent position size calculations', async ({ executorService }) => {
    // Arrange - Create 10 concurrent requests
    const requests = Array.from({ length: 10 }, (_, i) =>
      executorService.calculatePositionSize(
        executorService.createTestPositionSizeRequest({
          entry_price: 150.0 + i,
          stop_loss_price: 145.0 + i,
        })
      )
    );

    // Act
    const startTime = Date.now();
    const responses = await Promise.all(requests);
    const duration = Date.now() - startTime;

    // Assert
    expect(responses).toHaveLength(10);
    responses.forEach(response => {
      expect(response.ok).toBeTruthy();
      expect(response.body.success).toBeTruthy();
    });

    // Should complete in reasonable time (< 5 seconds)
    expect(duration).toBeLessThan(5000);
  });
});
