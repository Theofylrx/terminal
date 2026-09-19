import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config({ path: path.resolve(__dirname, '../.env') });

/**
 * Terminal Trading System - Playwright Test Configuration
 *
 * Supports:
 * - Frontend UI tests (React dashboard)
 * - API tests (FastAPI endpoints)
 * - Database tests (PostgreSQL + TimescaleDB)
 *
 * Test execution:
 * - npm run test:ui - Frontend tests
 * - npm run test:api - API endpoint tests
 * - npm run test:db - Database integration tests
 * - npm run test:e2e - End-to-end workflows
 * - npm run test:all - All tests
 */

const outputDir = './test-results/artifacts';

export default defineConfig({
  testDir: './specs',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Limit the number of failures on CI to save resources */
  maxFailures: process.env.CI ? 10 : undefined,

  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 4 : undefined,

  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'test-results/html-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/junit.xml' }],
    ['list'],
  ],

  // Folder for test artifacts such as screenshots, videos, traces, etc.
  outputDir: outputDir,

  // Each test is given 2 minutes (trading system operations can be slow)
  timeout: 120000,

  // Maximum time expect() should wait for
  expect: {
    timeout: 10000, // 10 seconds for assertions
  },

  /* Shared settings for all the projects below. */
  use: {
    /* Base URL for API tests */
    baseURL: process.env.API_BASE_URL || 'http://localhost:8000',

    /* Collect trace when retrying the failed test. */
    trace: 'on-first-retry',

    /* Collect screenshots on failure */
    screenshot: 'only-on-failure',

    /* Collect videos of the tests on failure */
    video: 'retain-on-failure',

    /* Extra HTTP headers for API tests */
    extraHTTPHeaders: {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
    },
  },

  /* Configure projects for different test types and browsers */
  projects: [
    // ========================================
    // Frontend UI Tests (React Dashboard)
    // ========================================
    {
      name: 'ui-chromium',
      testMatch: /.*\.ui\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        headless: true,
        viewport: { width: 1920, height: 1080 },
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
    },

    {
      name: 'ui-firefox',
      testMatch: /.*\.ui\.spec\.ts/,
      use: {
        ...devices['Desktop Firefox'],
        headless: true,
        viewport: { width: 1920, height: 1080 },
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
    },

    {
      name: 'ui-safari',
      testMatch: /.*\.ui\.spec\.ts/,
      use: {
        ...devices['Desktop Safari'],
        headless: true,
        viewport: { width: 1920, height: 1080 },
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
    },

    // ========================================
    // API Tests (FastAPI Endpoints)
    // ========================================
    {
      name: 'api',
      testMatch: /.*\.api\.spec\.ts/,
      use: {
        baseURL: process.env.API_BASE_URL || 'http://localhost:8000',
      },
    },

    // ========================================
    // Database Tests (PostgreSQL)
    // ========================================
    {
      name: 'database',
      testMatch: /.*\.db\.spec\.ts/,
      use: {
        // Database tests don't need a browser
      },
    },

    // ========================================
    // End-to-End Tests (Full Workflows)
    // ========================================
    {
      name: 'e2e-chromium',
      testMatch: /.*\.e2e\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        headless: true,
        viewport: { width: 1920, height: 1080 },
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
      dependencies: ['api', 'database'], // Run after API and DB tests pass
    },

    // ========================================
    // Mobile Tests (Optional)
    // ========================================
    {
      name: 'mobile-chrome',
      testMatch: /.*\.mobile\.spec\.ts/,
      use: {
        ...devices['Pixel 5'],
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
    },

    {
      name: 'mobile-safari',
      testMatch: /.*\.mobile\.spec\.ts/,
      use: {
        ...devices['iPhone 12'],
        baseURL: process.env.FRONTEND_URL || 'http://localhost:3000',
      },
    },
  ],

  /* Run your local dev server before starting the tests */
  // webServer: Disabled for now - services need to be started manually
  // webServer: process.env.CI ? undefined : [
  //   {
  //     command: 'cd ../agents/technical-analyst-service && python3 main.py',
  //     url: 'http://localhost:8000/health',
  //     timeout: 120 * 1000,
  //     reuseExistingServer: !process.env.CI,
  //   },
  // ],
});
