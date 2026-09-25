# Playwright Fixtures Guide

## Overview

This test framework uses Playwright's fixture system to manage Page Object Model (POM) instances, API services, and test user setup. Fixtures provide:

- **Automatic initialization** - No need to manually create/dispose objects
- **Type safety** - Full TypeScript support
- **Dependency injection** - Fixtures can depend on other fixtures
- **Cleanup** - Automatic disposal after tests
- **Reusability** - Share common setup across tests

## Available Fixtures

### Page Objects

#### `loginPage`
Provides an instance of `LoginPage` for the current test.

```typescript
test('Login test', async ({ loginPage }) => {
  await loginPage.gotoLogin();
  await loginPage.login('username', 'password');
});
```

#### `tradingPage`
Provides an instance of `TradingPage` for the current test.

```typescript
test('Trading test', async ({ tradingPage }) => {
  await tradingPage.gotoTrading();
  await tradingPage.executeOrder({ symbol: 'AAPL', quantity: 1 });
});
```

### API Services

#### `authService`
Provides an initialized `AuthService` instance. Automatically disposed after test.

```typescript
test('Auth API test', async ({ authService }) => {
  const response = await authService.login({ username, password });
  expect(response.ok).toBeTruthy();
});
```

#### `executorService`
Provides an initialized `ExecutorService` instance. Automatically disposed after test.

```typescript
test('Executor API test', async ({ executorService }) => {
  const response = await executorService.healthCheck();
  expect(response.body.status).toBe('healthy');
});
```

### User Management

#### `authenticatedUser`
Creates a test user via API and provides credentials + token. **Does NOT log in via UI**.

```typescript
test('API test with auth', async ({ authenticatedUser, executorService }) => {
  // User is created, token available
  console.log('User ID:', authenticatedUser.user.id);
  console.log('Token:', authenticatedUser.token);

  // Make authenticated API calls
  const response = await executorService.checkRisk({
    user_id: authenticatedUser.user.id,
    symbol: 'AAPL',
    quantity: 10
  });
});
```

#### `loggedInPage`
Creates a test user AND logs in via UI. Use for E2E tests that need authenticated state.

```typescript
test('E2E test', async ({ loggedInPage, tradingPage }) => {
  // User is already logged in via UI
  await tradingPage.gotoTrading(); // Navigate directly
  await tradingPage.executeOrder({ symbol: 'AAPL', quantity: 1 });
});
```

## Usage Examples

### API Tests

```typescript
import { test, expect } from '../../fixtures';

test.describe('Executor API', () => {
  test('Calculate position size', async ({ executorService }) => {
    const response = await executorService.calculatePositionSize({
      account_balance: 10000,
      entry_price: 150,
      stop_loss_price: 145
    });

    expect(response.ok).toBeTruthy();
    expect(response.body.quantity).toBeGreaterThan(0);
  });
});
```

### UI Tests

```typescript
import { test, expect } from '../../fixtures';

test.describe('Login Page', () => {
  test('Login with valid credentials', async ({ loginPage, authService }) => {
    const { credentials } = await authService.createTestUser();

    await loginPage.gotoLogin();
    await loginPage.login(credentials.username, credentials.password);
    await loginPage.validateSuccessfulLogin();
  });
});
```

### E2E Tests

```typescript
import { test, expect } from '../../fixtures';

test.describe('Trading Flow', () => {
  test('Complete order flow', async ({ loggedInPage, tradingPage }) => {
    // Already logged in via fixture
    await tradingPage.gotoTrading();
    await tradingPage.executeOrder({
      symbol: 'AAPL',
      quantity: 1,
      side: 'buy'
    });

    await tradingPage.waitForSuccessNotification();
  });
});
```

### Multiple Fixtures

```typescript
test('Complex test', async ({
  loginPage,
  tradingPage,
  authService,
  executorService
}) => {
  // Use multiple fixtures together
  const { credentials } = await authService.createTestUser();

  await loginPage.gotoLogin();
  await loginPage.login(credentials.username, credentials.password);

  await tradingPage.gotoTrading();

  // Verify via API
  const health = await executorService.healthCheck();
  expect(health.body.status).toBe('healthy');
});
```

## Best Practices

### 1. Import from Fixtures

❌ **DON'T:**
```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/loginPage';

test('My test', async ({ page }) => {
  const loginPage = new LoginPage(page);
  // ...
});
```

✅ **DO:**
```typescript
import { test, expect } from '../../fixtures';

test('My test', async ({ loginPage }) => {
  // loginPage is ready to use
});
```

### 2. Use Appropriate Fixtures

For **API-only tests**:
```typescript
test('API test', async ({ authService, executorService }) => {
  // No UI fixtures needed
});
```

For **UI tests requiring login**:
```typescript
test('UI test', async ({ loggedInPage, tradingPage }) => {
  // User is already logged in
});
```

For **UI tests testing login itself**:
```typescript
test('Login test', async ({ loginPage, authService }) => {
  // Don't use loggedInPage - you're testing login!
  const { credentials } = await authService.createTestUser();
  await loginPage.login(credentials.username, credentials.password);
});
```

### 3. No Manual Init/Dispose

❌ **DON'T:**
```typescript
test.beforeEach(async () => {
  const service = new AuthService();
  await service.init();
});

test.afterEach(async () => {
  await service.dispose();
});
```

✅ **DO:**
```typescript
test('My test', async ({ authService }) => {
  // Automatically initialized and disposed
});
```

### 4. Fixture Dependencies

Fixtures can depend on other fixtures:

```typescript
export const test = base.extend<MyFixtures>({
  // authenticatedUser depends on authService
  authenticatedUser: async ({ authService }, use) => {
    const user = await authService.createTestUser();
    await use(user);
  },

  // loggedInPage depends on authService and loginPage
  loggedInPage: async ({ authService, loginPage }, use) => {
    const { credentials } = await authService.createTestUser();
    await loginPage.login(credentials.username, credentials.password);
    await use();
  }
});
```

## Adding New Fixtures

To add new fixtures, update `/tests/fixtures/index.ts`:

```typescript
type TerminalFixtures = {
  // Existing fixtures...

  // Add new fixture
  myNewPage: MyNewPage;
  myNewService: MyNewService;
};

export const test = base.extend<TerminalFixtures>({
  // Existing fixtures...

  myNewPage: async ({ page }, use) => {
    const myPage = new MyNewPage(page);
    await use(myPage);
  },

  myNewService: async ({}, use) => {
    const service = new MyNewService();
    await service.init();
    await use(service);
    await service.dispose();
  }
});
```

## Migration Guide

### Old Pattern
```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/loginPage';
import { AuthService } from '../../lib/api/services/authService';

test.describe('Tests', () => {
  let loginPage: LoginPage;
  let authService: AuthService;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    authService = new AuthService();
    await authService.init();
  });

  test.afterEach(async () => {
    await authService.dispose();
  });

  test('My test', async () => {
    await loginPage.gotoLogin();
    // ...
  });
});
```

### New Pattern
```typescript
import { test, expect } from '../../fixtures';

test.describe('Tests', () => {
  test('My test', async ({ loginPage, authService }) => {
    await loginPage.gotoLogin();
    // ...
  });
});
```

## Benefits

1. **Less Boilerplate** - No beforeEach/afterEach
2. **Type Safety** - IntelliSense knows all available fixtures
3. **Automatic Cleanup** - No memory leaks
4. **Dependency Management** - Fixtures handle dependencies
5. **Parallel Execution** - Each test gets isolated instances
6. **Easier Testing** - Focus on test logic, not setup

---

For more information, see [Playwright Fixtures Documentation](https://playwright.dev/docs/test-fixtures).
