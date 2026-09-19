import { ApiClient, ApiResponse } from '../clients/apiClient';
import config from '../../config/config';

/**
 * Authentication Service
 *
 * Handles all authentication-related API requests:
 * - User registration
 * - User login
 * - Token refresh
 * - User profile
 */

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export class AuthService {
  private apiClient: ApiClient;

  constructor(baseURL: string = config.apiBaseUrl) {
    this.apiClient = new ApiClient(baseURL);
  }

  /**
   * Initialize API client
   */
  async init(): Promise<void> {
    await this.apiClient.init();
  }

  /**
   * Dispose API client
   */
  async dispose(): Promise<void> {
    await this.apiClient.dispose();
  }

  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<ApiResponse<UserResponse>> {
    return await this.apiClient.post<UserResponse>('/api/auth/register', data);
  }

  /**
   * Login user
   */
  async login(data: LoginRequest): Promise<ApiResponse<LoginResponse>> {
    // FastAPI OAuth2PasswordRequestForm expects form data
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    return await this.apiClient.post<LoginResponse>(
      '/api/auth/login',
      formData.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      }
    );
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(token: string): Promise<ApiResponse<UserResponse>> {
    this.apiClient.setAuthToken(token);
    return await this.apiClient.get<UserResponse>('/api/auth/me');
  }

  /**
   * Logout user
   */
  async logout(token: string): Promise<ApiResponse<{ message: string }>> {
    this.apiClient.setAuthToken(token);
    return await this.apiClient.post<{ message: string }>('/api/auth/logout', {});
  }

  /**
   * Helper: Register and login user
   */
  async registerAndLogin(data: RegisterRequest): Promise<{
    user: UserResponse;
    token: string;
  }> {
    // Register
    const registerResponse = await this.register(data);
    if (!registerResponse.ok) {
      throw new Error(`Registration failed: ${registerResponse.statusText}`);
    }

    // Login
    const loginResponse = await this.login({
      username: data.username,
      password: data.password,
    });

    if (!loginResponse.ok) {
      throw new Error(`Login failed: ${loginResponse.statusText}`);
    }

    return {
      user: registerResponse.body,
      token: loginResponse.body.access_token,
    };
  }

  /**
   * Helper: Create test user with unique credentials
   */
  async createTestUser(prefix: string = 'test'): Promise<{
    user: UserResponse;
    token: string;
    credentials: RegisterRequest;
  }> {
    const timestamp = Date.now();
    const credentials: RegisterRequest = {
      username: `${prefix}_${timestamp}`,
      email: `${prefix}_${timestamp}@terminal.test`,
      password: `Test${timestamp}!`,
      first_name: 'Test',
      last_name: 'User',
    };

    const { user, token } = await this.registerAndLogin(credentials);

    return { user, token, credentials };
  }
}
