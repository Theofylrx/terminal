import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './basePage';

/**
 * Login Page Object
 *
 * Handles all interactions with the login page
 */
export class LoginPage extends BasePage {
  // Locators
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly pageTitle: Locator;
  readonly registerLink: Locator;
  readonly forgotPasswordLink: Locator;

  constructor(page: Page) {
    super(page);

    // Initialize locators
    this.usernameInput = page.locator('input[name="username"], input[id="username"], input[type="email"]');
    this.passwordInput = page.locator('input[name="password"], input[id="password"], input[type="password"]');
    this.loginButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")');
    this.errorMessage = page.locator('[data-testid="error-message"], .error-message, .alert-error');
    this.pageTitle = page.locator('h1, h2').first();
    this.registerLink = page.locator('a:has-text("Register"), a:has-text("Sign up")');
    this.forgotPasswordLink = page.locator('a:has-text("Forgot password")');
  }

  /**
   * Navigate to login page
   */
  async gotoLogin(): Promise<void> {
    await this.goto('/login');
  }

  /**
   * Validate login page is loaded
   */
  async validateLoginPage(): Promise<void> {
    await expect(this.usernameInput).toBeVisible();
    await expect(this.passwordInput).toBeVisible();
    await expect(this.loginButton).toBeVisible();
  }

  /**
   * Enter username
   */
  async enterUsername(username: string): Promise<void> {
    await this.fillInput(this.usernameInput, username);
  }

  /**
   * Enter password
   */
  async enterPassword(password: string): Promise<void> {
    await this.fillInput(this.passwordInput, password);
  }

  /**
   * Click login button
   */
  async clickLogin(): Promise<void> {
    await this.loginButton.click();
  }

  /**
   * Perform login
   */
  async login(username: string, password: string): Promise<void> {
    await this.enterUsername(username);
    await this.enterPassword(password);
    await this.clickLogin();
  }

  /**
   * Validate error message is displayed
   */
  async validateErrorMessage(expectedMessage?: string): Promise<void> {
    await expect(this.errorMessage).toBeVisible();

    if (expectedMessage) {
      await expect(this.errorMessage).toHaveText(expectedMessage);
    }
  }

  /**
   * Validate successful login (redirected to dashboard)
   */
  async validateSuccessfulLogin(): Promise<void> {
    await this.waitForPageLoad();
    await this.validatePageURL('/dashboard');
  }

  /**
   * Click register link
   */
  async clickRegister(): Promise<void> {
    await this.registerLink.click();
  }

  /**
   * Click forgot password link
   */
  async clickForgotPassword(): Promise<void> {
    await this.forgotPasswordLink.click();
  }
}
