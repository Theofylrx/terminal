import { test, expect } from '../../fixtures';
import config from '../../lib/config/config';

/**
 * Login UI Tests
 *
 * Tests the login page functionality:
 * - Page load and elements
 * - Successful login
 * - Failed login
 * - Validation messages
 *
 * Tags: @ui @login @critical
 */

test.describe('Login Page', () => {
  test.beforeEach(async ({ loginPage }) => {
    // Navigate to login page
    await loginPage.gotoLogin();
  });

  test('@ui @login @critical - Login page loads correctly', async ({ loginPage }) => {
    // Assert - All elements visible
    await loginPage.validateLoginPage();

    // Validate page title
    await loginPage.validateTitle('Terminal');
  });

  test('@ui @login @critical - Successful login redirects to dashboard', async ({ loginPage, authService }) => {
    // Arrange - Create test user via API
    const { credentials } = await authService.createTestUser('ui_test');

    // Act - Login via UI
    await loginPage.login(credentials.username, credentials.password);

    // Assert - Redirected to dashboard
    await loginPage.validateSuccessfulLogin();
  });

  test('@ui @login @critical - Failed login shows error message', async ({ loginPage }) => {
    // Act - Login with invalid credentials
    await loginPage.login('invalid_user', 'invalid_password');

    // Assert - Error message displayed
    await loginPage.validateErrorMessage();
  });

  test('@ui @login - Empty username validation', async ({ loginPage }) => {
    // Act
    await loginPage.enterPassword('somepassword');
    await loginPage.clickLogin();

    // Assert - Validation error (browser HTML5 validation or custom)
    await expect(loginPage.usernameInput).toHaveAttribute('required', '');
  });

  test('@ui @login - Empty password validation', async ({ loginPage }) => {
    // Act
    await loginPage.enterUsername('someuser');
    await loginPage.clickLogin();

    // Assert - Validation error
    await expect(loginPage.passwordInput).toHaveAttribute('required', '');
  });

  test('@ui @login @smoke - Login button is enabled', async ({ loginPage }) => {
    // Assert
    await expect(loginPage.loginButton).toBeEnabled();
  });

  test('@ui @login - Password field is masked', async ({ loginPage }) => {
    // Assert
    await expect(loginPage.passwordInput).toHaveAttribute('type', 'password');
  });

  test('@ui @login - Login with Enter key', async ({ page, loginPage, authService }) => {
    // Arrange
    const { credentials } = await authService.createTestUser('ui_enter_test');

    // Act
    await loginPage.enterUsername(credentials.username);
    await loginPage.enterPassword(credentials.password);
    await page.keyboard.press('Enter');

    // Assert
    await loginPage.validateSuccessfulLogin();
  });

  test('@ui @login - Register link navigation', async ({ loginPage }) => {
    // Act
    await loginPage.clickRegister();

    // Assert
    await loginPage.validatePageURL('/register');
  });

  test('@ui @login - Forgot password link navigation', async ({ loginPage }) => {
    // Skip if forgot password not implemented
    test.skip(!await loginPage.isVisible(loginPage.forgotPasswordLink), 'Forgot password not implemented');

    // Act
    await loginPage.clickForgotPassword();

    // Assert
    await loginPage.validatePageURL('/forgot-password');
  });

  test('@ui @login - Login persists session', async ({ loginPage, authService }) => {
    // Arrange
    const { credentials } = await authService.createTestUser('session_test');

    // Act - Login
    await loginPage.login(credentials.username, credentials.password);
    await loginPage.validateSuccessfulLogin();

    // Reload page
    await loginPage.reload();

    // Assert - Still logged in (not redirected to login)
    await loginPage.validatePageURL('/dashboard');
  });

  test('@ui @login - Logout clears session', async ({ page, loginPage, authService }) => {
    // Arrange
    const { credentials } = await authService.createTestUser('logout_test');

    // Login
    await loginPage.login(credentials.username, credentials.password);
    await loginPage.validateSuccessfulLogin();

    // Act - Logout (assuming logout button exists in dashboard)
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), a:has-text("Logout")');

    if (await logoutButton.isVisible()) {
      await logoutButton.click();

      // Assert - Redirected to login
      await loginPage.validatePageURL('/login');

      // Try to access dashboard directly
      await page.goto(`${config.frontendUrl}/dashboard`);

      // Should be redirected back to login
      await loginPage.validatePageURL('/login');
    } else {
      test.skip(true, 'Logout button not found');
    }
  });
});
