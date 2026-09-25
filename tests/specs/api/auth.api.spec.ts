import { test, expect } from '../../fixtures';

/**
 * Authentication API Tests
 *
 * Tests all authentication endpoints:
 * - User registration
 * - User login
 * - Get current user
 * - Logout
 *
 * Tags: @api @auth @critical
 */

test.describe('Authentication API', () => {

  test('@api @auth @critical - User Registration - Success', async ({ authService }) => {
    // Arrange
    const timestamp = Date.now();
    const registerData = {
      username: `testuser_${timestamp}`,
      email: `testuser_${timestamp}@terminal.test`,
      password: 'TestPassword123!',
      first_name: 'Test',
      last_name: 'User',
    };

    // Act
    const response = await authService.register(registerData);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(201);
    expect(response.body).toHaveProperty('id');
    expect(response.body).toHaveProperty('username', registerData.username);
    expect(response.body).toHaveProperty('email', registerData.email);
    expect(response.body).toHaveProperty('is_active', true);
    expect(response.body).not.toHaveProperty('password'); // Password should not be returned
  });

  test('@api @auth @critical - User Registration - Duplicate Email', async ({ authService }) => {
    // Arrange
    const timestamp = Date.now();
    const registerData = {
      username: `testuser_${timestamp}`,
      email: `testuser_${timestamp}@terminal.test`,
      password: 'TestPassword123!',
    };

    // Register first user
    await authService.register(registerData);

    // Act - Try to register with same email
    const response = await authService.register({
      ...registerData,
      username: `different_${timestamp}`,
    });

    // Assert
    expect(response.ok).toBeFalsy();
    expect(response.status).toBe(400);
    expect(response.body).toHaveProperty('detail');
    expect(response.body.detail).toContain('already registered');
  });

  test('@api @auth @critical - User Login - Success', async ({ authService }) => {
    // Arrange
    const { credentials } = await authService.createTestUser();

    // Act
    const response = await authService.login({
      username: credentials.username,
      password: credentials.password,
    });

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('access_token');
    expect(response.body).toHaveProperty('token_type', 'bearer');
    expect(response.body).toHaveProperty('expires_in');
    expect(typeof response.body.access_token).toBe('string');
    expect(response.body.access_token.length).toBeGreaterThan(0);
  });

  test('@api @auth @critical - User Login - Invalid Credentials', async ({ authService }) => {
    // Act
    const response = await authService.login({
      username: 'nonexistent_user',
      password: 'wrong_password',
    });

    // Assert
    expect(response.ok).toBeFalsy();
    expect(response.status).toBe(401);
    expect(response.body).toHaveProperty('detail');
  });

  test('@api @auth @critical - Get Current User - Success', async ({ authService }) => {
    // Arrange
    const { user, token } = await authService.createTestUser();

    // Act
    const response = await authService.getCurrentUser(token);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('id', user.id);
    expect(response.body).toHaveProperty('username', user.username);
    expect(response.body).toHaveProperty('email', user.email);
  });

  test('@api @auth - Get Current User - Unauthorized', async ({ authService }) => {
    // Act
    const response = await authService.getCurrentUser('invalid_token');

    // Assert
    expect(response.ok).toBeFalsy();
    expect(response.status).toBe(401);
  });

  test('@api @auth - Logout - Success', async ({ authService }) => {
    // Arrange
    const { token } = await authService.createTestUser();

    // Act
    const response = await authService.logout(token);

    // Assert
    expect(response.ok).toBeTruthy();
    expect(response.status).toBe(200);
    expect(response.body).toHaveProperty('message');
  });

  test('@api @auth @smoke - JWT Token Format', async ({ authService }) => {
    // Arrange
    const { credentials } = await authService.createTestUser();

    // Act
    const response = await authService.login({
      username: credentials.username,
      password: credentials.password,
    });

    // Assert
    expect(response.ok).toBeTruthy();

    const token = response.body.access_token;

    // JWT should have 3 parts separated by dots
    const parts = token.split('.');
    expect(parts.length).toBe(3);

    // Each part should be base64 encoded
    parts.forEach((part) => {
      expect(part.length).toBeGreaterThan(0);
    });
  });

  test('@api @auth - Password Requirements Validation', async ({ authService }) => {
    // Arrange
    const timestamp = Date.now();
    const weakPasswordData = {
      username: `testuser_${timestamp}`,
      email: `testuser_${timestamp}@terminal.test`,
      password: 'weak', // Weak password
    };

    // Act
    const response = await authService.register(weakPasswordData);

    // Assert
    expect(response.ok).toBeFalsy();
    // Expecting validation error for weak password
  });
});
