import { Page, Locator } from '@playwright/test';
import { BasePage } from './basePage';

/**
 * Trading Page Object
 *
 * Represents the trading dashboard page with:
 * - Order entry form
 * - Position display
 * - Risk metrics
 * - Trade execution
 */
export class TradingPage extends BasePage {
  // Navigation
  readonly dashboardLink: Locator;
  readonly tradingLink: Locator;

  // Order Entry Form
  readonly symbolInput: Locator;
  readonly quantityInput: Locator;
  readonly sideSelect: Locator;
  readonly orderTypeSelect: Locator;
  readonly limitPriceInput: Locator;
  readonly stopLossInput: Locator;
  readonly takeProfitInput: Locator;
  readonly submitOrderButton: Locator;

  // Position Display
  readonly positionsTable: Locator;
  readonly positionRows: Locator;
  readonly openPositionsCount: Locator;

  // Risk Metrics
  readonly accountBalanceLabel: Locator;
  readonly totalRiskLabel: Locator;
  readonly availableRiskLabel: Locator;

  // Notifications
  readonly successNotification: Locator;
  readonly errorNotification: Locator;
  readonly warningNotification: Locator;

  // Modals
  readonly confirmationModal: Locator;
  readonly confirmButton: Locator;
  readonly cancelButton: Locator;

  constructor(page: Page) {
    super(page);

    // Navigation
    this.dashboardLink = page.locator('a[href*="/dashboard"], button:has-text("Dashboard")');
    this.tradingLink = page.locator('a[href*="/trading"], button:has-text("Trading"), a:has-text("Trade")');

    // Order Entry Form
    this.symbolInput = page.locator('input[name="symbol"], input[placeholder*="Symbol"], input[id="symbol"]');
    this.quantityInput = page.locator('input[name="quantity"], input[placeholder*="Quantity"], input[id="quantity"]');
    this.sideSelect = page.locator('select[name="side"], select[id="side"], button[role="combobox"]:has-text("Buy"), button[role="combobox"]:has-text("Sell")');
    this.orderTypeSelect = page.locator('select[name="orderType"], select[id="orderType"], select[name="order_type"]');
    this.limitPriceInput = page.locator('input[name="limitPrice"], input[name="limit_price"], input[placeholder*="Limit"]');
    this.stopLossInput = page.locator('input[name="stopLoss"], input[name="stop_loss"], input[placeholder*="Stop Loss"]');
    this.takeProfitInput = page.locator('input[name="takeProfit"], input[name="take_profit"], input[placeholder*="Take Profit"]');
    this.submitOrderButton = page.locator('button:has-text("Submit"), button:has-text("Execute"), button:has-text("Place Order"), button[type="submit"]');

    // Position Display
    this.positionsTable = page.locator('table:has-text("Positions"), div:has-text("Open Positions")');
    this.positionRows = page.locator('table tbody tr, div[role="row"]');
    this.openPositionsCount = page.locator('span:has-text("Open Positions"), h3:has-text("Positions")');

    // Risk Metrics
    this.accountBalanceLabel = page.locator('span:has-text("Balance"), div:has-text("Account Balance")');
    this.totalRiskLabel = page.locator('span:has-text("Total Risk"), div:has-text("Risk")');
    this.availableRiskLabel = page.locator('span:has-text("Available"), div:has-text("Available Risk")');

    // Notifications
    this.successNotification = page.locator('.toast.success, .notification.success, [role="alert"]:has-text("Success")');
    this.errorNotification = page.locator('.toast.error, .notification.error, [role="alert"]:has-text("Error")');
    this.warningNotification = page.locator('.toast.warning, .notification.warning, [role="alert"]:has-text("Warning")');

    // Modals
    this.confirmationModal = page.locator('[role="dialog"], .modal, .confirmation-modal');
    this.confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Yes")');
    this.cancelButton = page.locator('button:has-text("Cancel"), button:has-text("No")');
  }

  /**
   * Navigate to trading page
   */
  async gotoTrading(): Promise<void> {
    await this.goto('/trading');
    await this.waitForPageLoad();
  }

  /**
   * Fill order entry form
   */
  async fillOrderForm(order: {
    symbol: string;
    quantity: number;
    side?: 'buy' | 'sell';
    orderType?: 'market' | 'limit';
    limitPrice?: number;
    stopLoss?: number;
    takeProfit?: number;
  }): Promise<void> {
    // Enter symbol
    await this.fillInput(this.symbolInput, order.symbol);

    // Enter quantity
    await this.fillInput(this.quantityInput, order.quantity.toString());

    // Select side if provided
    if (order.side) {
      if (await this.sideSelect.getAttribute('role') === 'combobox') {
        await this.sideSelect.click();
        await this.page.locator(`li:has-text("${order.side}"), option:has-text("${order.side}")`).click();
      } else {
        await this.sideSelect.selectOption(order.side);
      }
    }

    // Select order type if provided
    if (order.orderType && await this.orderTypeSelect.isVisible()) {
      await this.orderTypeSelect.selectOption(order.orderType);
    }

    // Enter limit price if provided
    if (order.limitPrice && await this.limitPriceInput.isVisible()) {
      await this.fillInput(this.limitPriceInput, order.limitPrice.toString());
    }

    // Enter stop loss if provided
    if (order.stopLoss && await this.stopLossInput.isVisible()) {
      await this.fillInput(this.stopLossInput, order.stopLoss.toString());
    }

    // Enter take profit if provided
    if (order.takeProfit && await this.takeProfitInput.isVisible()) {
      await this.fillInput(this.takeProfitInput, order.takeProfit.toString());
    }
  }

  /**
   * Submit order
   */
  async submitOrder(): Promise<void> {
    await this.submitOrderButton.click();
  }

  /**
   * Confirm order in modal (if appears)
   */
  async confirmOrderIfModalAppears(timeout: number = 5000): Promise<void> {
    try {
      await this.confirmationModal.waitFor({ state: 'visible', timeout });
      await this.confirmButton.click();
    } catch {
      // Modal didn't appear, continue
    }
  }

  /**
   * Execute order (fill form and submit)
   */
  async executeOrder(order: {
    symbol: string;
    quantity: number;
    side?: 'buy' | 'sell';
    orderType?: 'market' | 'limit';
    limitPrice?: number;
    stopLoss?: number;
    takeProfit?: number;
  }): Promise<void> {
    await this.fillOrderForm(order);
    await this.submitOrder();
    await this.confirmOrderIfModalAppears();
  }

  /**
   * Wait for success notification
   */
  async waitForSuccessNotification(timeout: number = 10000): Promise<void> {
    await this.waitForElement(this.successNotification, timeout);
  }

  /**
   * Wait for error notification
   */
  async waitForErrorNotification(timeout: number = 10000): Promise<void> {
    await this.waitForElement(this.errorNotification, timeout);
  }

  /**
   * Get notification text
   */
  async getNotificationText(): Promise<string> {
    const notification = this.page.locator('[role="alert"], .toast, .notification').first();
    return await this.getElementText(notification);
  }

  /**
   * Get open positions count
   */
  async getOpenPositionsCount(): Promise<number> {
    const rows = await this.positionRows.count();
    return rows;
  }

  /**
   * Get account balance
   */
  async getAccountBalance(): Promise<string> {
    return await this.getElementText(this.accountBalanceLabel);
  }

  /**
   * Validate trading page is loaded
   */
  async validateTradingPageLoaded(): Promise<void> {
    await this.waitForElement(this.symbolInput);
    await this.waitForElement(this.submitOrderButton);
  }

  /**
   * Navigate to dashboard
   */
  async gotoDashboard(): Promise<void> {
    await this.dashboardLink.click();
    await this.waitForPageLoad();
  }

  /**
   * Check if position exists for symbol
   */
  async hasPositionForSymbol(symbol: string): Promise<boolean> {
    const positionCell = this.page.locator(`td:has-text("${symbol}"), div:has-text("${symbol}")`);
    return await positionCell.isVisible();
  }

  /**
   * Wait for position to appear
   */
  async waitForPosition(symbol: string, timeout: number = 15000): Promise<void> {
    const positionCell = this.page.locator(`td:has-text("${symbol}"), div:has-text("${symbol}")`);
    await this.waitForElement(positionCell, timeout);
  }
}
