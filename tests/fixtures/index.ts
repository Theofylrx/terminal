import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/loginPage';
import { TradingPage } from '../pages/tradingPage';
import { AuthService } from '../lib/api/services/authService';
import { ExecutorService } from '../lib/api/services/executorService';

/**
 * Terminal Trading System Test Fixtures
 *
 * Provides reusable fixtures for:
 * - Page Objects (LoginPage, TradingPage, etc.)
 * - API Services (AuthService, ExecutorService, etc.)
 * - Test Users (authenticated users, tokens)
 *
 * Usage:
 * import { test, expect } from '../fixtures';
 *
 * test('My test', async ({ loginPage, tradingPage, authService }) => {
 *   // Use fixtures directly
 * });
 */

type TerminalFixtures = {
  // Page Objects
  loginPage: LoginPage;
  tradingPage: TradingPage;

  // API Services
  authService: AuthService;
  executorService: ExecutorService;

  // Authenticated User
  authenticatedUser: {
    user: any;
    credentials: { username: string; password: string };
    token: string;
  };

  // Logged In Page (automatically logged in via UI)
  loggedInPage: void;
};

/**
 * Extend Playwright test with custom fixtures
 */
export const test = base.extend<TerminalFixtures>({
  /**
   * Login Page fixture
   * Automatically initializes LoginPage with current page
   */
  loginPage: async ({ page }, use) => {
    const loginPage = new LoginPage(page);
    await use(loginPage);
  },

  /**
   * Trading Page fixture
   * Automatically initializes TradingPage with current page
   */
  tradingPage: async ({ page }, use) => {
    const tradingPage = new TradingPage(page);
    await use(tradingPage);
  },

  /**
   * Auth Service fixture
   * Automatically initializes and disposes AuthService
   */
  authService: async ({}, use) => {
    const authService = new AuthService();
    await authService.init();
    await use(authService);
    await authService.dispose();
  },

  /**
   * Executor Service fixture
   * Automatically initializes and disposes ExecutorService
   */
  executorService: async ({}, use) => {
    const executorService = new ExecutorService();
    await executorService.init();
    await use(executorService);
    await executorService.dispose();
  },

  /**
   * Authenticated User fixture
   * Creates a test user via API and provides credentials + token
   * Does NOT log in via UI - use for API tests or manual UI login
   */
  authenticatedUser: async ({ authService }, use) => {
    const timestamp = Date.now();
    const result = await authService.createTestUser(`test_user_${timestamp}`);

    await use({
      user: result.user,
      credentials: result.credentials,
      token: result.token,
    });

    // Cleanup: delete test user if needed
    // await authService.deleteUser(result.user.id);
  },

  /**
   * Logged In Page fixture
   * Automatically creates user, logs in via UI, and navigates to dashboard
   * Use for E2E tests that need authenticated UI state
   */
  loggedInPage: async ({ page, authService, loginPage }, use) => {
    // Create test user
    const timestamp = Date.now();
    const { credentials } = await authService.createTestUser(`ui_user_${timestamp}`);

    // Login via UI
    await loginPage.gotoLogin();
    await loginPage.login(credentials.username, credentials.password);
    await loginPage.validateSuccessfulLogin();

    await use();

    // Cleanup happens automatically when page closes
  },
});

/**
 * Re-export expect from Playwright
 */
export { expect } from '@playwright/test';
