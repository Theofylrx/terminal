# Terminal Trading System - Test Framework

Comprehensive test automation framework for the Terminal Trading System using **Playwright** and **TypeScript**.

## 📋 Features

- ✅ **UI Tests** - Frontend React dashboard tests with Page Object Model
- ✅ **API Tests** - FastAPI endpoint tests with service layer abstraction
- ✅ **Database Tests** - PostgreSQL integration tests with data isolation verification
- ✅ **Multi-Browser Support** - Chrome, Firefox, Safari
- ✅ **Mobile Testing** - Responsive design validation
- ✅ **Tag-Based Execution** - Run specific test suites (@critical, @smoke, @api, @ui, @database)
- ✅ **Parallel Execution** - Fast test execution with parallel workers
- ✅ **Rich Reporting** - HTML, JSON, JUnit reports
- ✅ **CI/CD Ready** - Docker support and GitHub Actions integration

## 🏗️ Architecture

```
tests/
├── lib/                          # Reusable test library
│   ├── api/                      # API testing utilities
│   │   ├── clients/              # API clients (apiClient.ts)
│   │   └── services/             # Service layer (authService.ts, etc.)
│   ├── database/                 # Database testing utilities
│   │   └── clients/              # DB clients (dbClient.ts)
│   ├── config/                   # Configuration (config.ts)
│   ├── models/                   # Data models
│   └── helpers/                  # Test helpers
├── pages/                        # Page Object Model
│   ├── basePage.ts               # Base page with common methods
│   ├── loginPage.ts              # Login page
│   └── ...                       # Other pages
├── specs/                        # Test specifications
│   ├── api/                      # API tests
│   │   └── *.api.spec.ts
│   ├── ui/                       # UI tests
│   │   └── *.ui.spec.ts
│   ├── database/                 # Database tests
│   │   └── *.db.spec.ts
│   └── e2e/                      # End-to-end tests
│       └── *.e2e.spec.ts
├── fixtures/                     # Test fixtures
├── playwright.config.ts          # Playwright configuration
├── package.json                  # Dependencies and scripts
└── tsconfig.json                 # TypeScript configuration
```

## 🚀 Getting Started

### Prerequisites

- Node.js >= 18.0.0
- npm or yarn
- PostgreSQL (for database tests)
- Terminal services running (API, Frontend)

### Installation

```bash
# Navigate to tests directory
cd tests

# Install dependencies
npm install

# Install Playwright browsers
npm run install:browsers

# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Configuration

Edit `.env` file with your environment settings:

```env
# API URLs
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=terminal
DB_USER=postgres
DB_PASSWORD=postgres

# Test users will be created automatically
```

## 🧪 Running Tests

### Quick Start

```bash
# Run all tests
npm run test:all

# Run UI tests
npm run test:ui

# Run API tests
npm run test:api

# Run database tests
npm run test:db

# Run end-to-end tests
npm run test:e2e

# Run critical tests only
npm run test:critical

# Run smoke tests
npm run test:smoke
```

### Specific Test Types

```bash
# UI tests on all browsers
npm run test:ui:all-browsers

# API authentication tests
npm run test:api:auth

# API signal generation tests
npm run test:api:signals

# Database model tests
npm run test:db:models

# Database isolation tests
npm run test:db:isolation

# E2E trading flow
npm run test:e2e:trading-flow

# E2E analysis flow
npm run test:e2e:analysis-flow
```

### Debug Mode

```bash
# Debug all tests
npm run test:debug

# Debug UI tests with Playwright Inspector
npm run test:ui:debug

# Run tests in headed mode (see browser)
npm run test:headed
```

### View Reports

```bash
# Open HTML report
npm run test:report
```

## 📝 Writing Tests

### UI Test Example

```typescript
import { test, expect } from '@playwright/test';
import { LoginPage } from '../../pages/loginPage';

test('@ui @login @critical - Successful login', async ({ page }) => {
  const loginPage = new LoginPage(page);

  await loginPage.gotoLogin();
  await loginPage.login('testuser', 'password123');
  await loginPage.validateSuccessfulLogin();
});
```

### API Test Example

```typescript
import { test, expect } from '@playwright/test';
import { AuthService } from '../../lib/api/services/authService';

test('@api @auth @critical - User login returns token', async () => {
  const authService = new AuthService();
  await authService.init();

  const response = await authService.login({
    username: 'testuser',
    password: 'password123',
  });

  expect(response.ok).toBeTruthy();
  expect(response.body).toHaveProperty('access_token');

  await authService.dispose();
});
```

### Database Test Example

```typescript
import { test, expect } from '@playwright/test';
import { DatabaseClient } from '../../lib/database/clients/dbClient';

test('@database @isolation @critical - User data isolation', async () => {
  const db = new DatabaseClient();
  await db.connect();

  const user1Signals = await db.queryAll(
    'SELECT * FROM signals WHERE user_id = $1',
    [user1Id]
  );

  expect(user1Signals.every((s) => s.user_id === user1Id)).toBeTruthy();

  await db.disconnect();
});
```

## 🏷️ Test Tags

Organize and run tests by tags:

- `@critical` - Must-pass tests for deployments
- `@smoke` - Quick smoke tests
- `@api` - API tests
- `@ui` - UI tests
- `@database` - Database tests
- `@e2e` - End-to-end tests
- `@mobile` - Mobile tests
- `@auth` - Authentication tests
- `@signals` - Signal generation tests
- `@trading` - Trading flow tests
- `@isolation` - Data isolation tests

```bash
# Run critical tests only
npx playwright test --grep "@critical"

# Run API authentication tests
npx playwright test --grep "@api.*@auth"

# Run all tests except mobile
npx playwright test --grep-invert "@mobile"
```

## 🗄️ Database Management

```bash
# Start PostgreSQL
npm run db:start

# Stop PostgreSQL
npm run db:stop

# Restart PostgreSQL
npm run db:restart

# Connect to database
npm run db:connect

# Seed test data
npm run db:seed

# Clean test data
npm run db:clean
```

## 🐳 Docker Support

```bash
# Start all services
npm run services:start

# Stop all services
npm run services:stop

# Restart all services
npm run services:restart

# View service logs
npm run services:logs
```

## 📊 Test Reports

After running tests, reports are generated in:

- **HTML Report**: `test-results/html-report/`
- **JSON Report**: `test-results/results.json`
- **JUnit Report**: `test-results/junit.xml`
- **Screenshots**: `test-results/screenshots/` (on failure)
- **Videos**: `test-results/` (on failure)
- **Traces**: `test-results/` (on retry)

## 🔧 Configuration

### Playwright Configuration

Edit `playwright.config.ts` to customize:
- Test timeout
- Parallel workers
- Retry strategy
- Screenshot/video capture
- Browser configuration

### TypeScript Configuration

Edit `tsconfig.json` for:
- Path aliases
- Compiler options
- Include/exclude patterns

## 🎯 Best Practices

### Page Object Model

✅ **DO:**
- Extend `BasePage` for all page objects
- Use descriptive locator names
- Create reusable methods
- Keep assertions in tests, not pages

❌ **DON'T:**
- Put assertions in page objects
- Hardcode URLs
- Use `page.waitForTimeout()` (use proper waits)

### API Tests

✅ **DO:**
- Use service layer abstraction
- Initialize and dispose clients properly
- Use test-specific users
- Clean up test data

❌ **DON'T:**
- Share credentials across tests
- Skip authentication
- Leave orphaned test data

### Database Tests

✅ **DO:**
- Test multi-tenant isolation
- Use transactions for data cleanup
- Verify indexes exist
- Test cascade deletes

❌ **DON'T:**
- Use production database
- Skip cleanup
- Hardcode user IDs

## 🚀 CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd tests && npm install
      - run: npx playwright install --with-deps
      - run: npm run test:all
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: tests/test-results/
```

## 📚 Resources

- [Playwright Documentation](https://playwright.dev)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)
- [Testing Best Practices](https://playwright.dev/docs/best-practices)

## 🤝 Contributing

1. Write tests for new features
2. Follow existing patterns
3. Use appropriate tags
4. Update documentation
5. Ensure tests pass before committing

## 📄 License

ISC

---

**Happy Testing! 🎭**
