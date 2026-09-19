import { expect, Page, Locator } from '@playwright/test';
import config from '../lib/config/config';

/**
 * Base Page Object
 *
 * Provides common functionality for all page objects:
 * - Navigation
 * - Waiting strategies
 * - Common assertions
 * - Screenshot capture
 */
export class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  /**
   * Navigate to a path
   * @param path - Relative path (e.g., '/dashboard')
   */
  async goto(path: string = ''): Promise<void> {
    const url = path ? `${config.frontendUrl}${path}` : config.frontendUrl;
    await this.page.goto(url, { waitUntil: 'domcontentloaded' });
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * Validate current URL contains expected path
   */
  async validatePageURL(expectedPath: string): Promise<void> {
    expect(this.page.url()).toContain(expectedPath);
  }

  /**
   * Wait for element to be visible
   */
  async waitForElement(locator: Locator, timeout: number = config.timeouts.medium): Promise<void> {
    await locator.waitFor({ state: 'visible', timeout });
  }

  /**
   * Wait for element to be hidden
   */
  async waitForElementHidden(locator: Locator, timeout: number = config.timeouts.medium): Promise<void> {
    await locator.waitFor({ state: 'hidden', timeout });
  }

  /**
   * Get element text
   */
  async getElementText(locator: Locator): Promise<string> {
    return await locator.textContent() || '';
  }

  /**
   * Check if element is visible
   */
  async isVisible(locator: Locator): Promise<boolean> {
    return await locator.isVisible();
  }

  /**
   * Check if element is enabled
   */
  async isEnabled(locator: Locator): Promise<boolean> {
    return await locator.isEnabled();
  }

  /**
   * Click element with retry
   */
  async clickWithRetry(locator: Locator, retries: number = 3): Promise<void> {
    for (let i = 0; i < retries; i++) {
      try {
        await locator.click({ timeout: config.timeouts.short });
        return;
      } catch (error) {
        if (i === retries - 1) throw error;
        await this.page.waitForTimeout(1000);
      }
    }
  }

  /**
   * Fill input with clear
   */
  async fillInput(locator: Locator, value: string): Promise<void> {
    await locator.clear();
    await locator.fill(value);
  }

  /**
   * Take screenshot with name
   */
  async takeScreenshot(name: string): Promise<void> {
    await this.page.screenshot({
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true,
    });
  }

  /**
   * Wait for API response
   */
  async waitForAPIResponse(urlPattern: string | RegExp, timeout: number = config.timeouts.apiRequest): Promise<any> {
    const response = await this.page.waitForResponse(
      (response) => {
        const url = response.url();
        if (typeof urlPattern === 'string') {
          return url.includes(urlPattern);
        }
        return urlPattern.test(url);
      },
      { timeout }
    );
    return await response.json();
  }

  /**
   * Wait for navigation
   */
  async waitForNavigation(timeout: number = config.timeouts.medium): Promise<void> {
    await this.page.waitForNavigation({ timeout });
  }

  /**
   * Reload page
   */
  async reload(): Promise<void> {
    await this.page.reload({ waitUntil: 'domcontentloaded' });
  }

  /**
   * Get page title
   */
  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  /**
   * Validate page title
   */
  async validateTitle(expectedTitle: string): Promise<void> {
    const title = await this.getTitle();
    expect(title).toContain(expectedTitle);
  }

  /**
   * Execute JavaScript in page context
   */
  async executeScript<T>(script: string): Promise<T> {
    return await this.page.evaluate(script);
  }

  /**
   * Get local storage item
   */
  async getLocalStorageItem(key: string): Promise<string | null> {
    return await this.page.evaluate((key) => localStorage.getItem(key), key);
  }

  /**
   * Set local storage item
   */
  async setLocalStorageItem(key: string, value: string): Promise<void> {
    await this.page.evaluate(
      ({ key, value }) => localStorage.setItem(key, value),
      { key, value }
    );
  }

  /**
   * Clear local storage
   */
  async clearLocalStorage(): Promise<void> {
    await this.page.evaluate(() => localStorage.clear());
  }

  /**
   * Wait for element count
   */
  async waitForElementCount(locator: Locator, count: number, timeout: number = config.timeouts.medium): Promise<void> {
    await expect(locator).toHaveCount(count, { timeout });
  }

  /**
   * Scroll element into view
   */
  async scrollIntoView(locator: Locator): Promise<void> {
    await locator.scrollIntoViewIfNeeded();
  }

  /**
   * Hover over element
   */
  async hover(locator: Locator): Promise<void> {
    await locator.hover();
  }

  /**
   * Select option from dropdown
   */
  async selectOption(locator: Locator, value: string): Promise<void> {
    await locator.selectOption(value);
  }

  /**
   * Get all text contents from elements
   */
  async getAllTextContents(locator: Locator): Promise<string[]> {
    return await locator.allTextContents();
  }

  /**
   * Wait for timeout (use sparingly)
   */
  async wait(milliseconds: number): Promise<void> {
    await this.page.waitForTimeout(milliseconds);
  }
}
