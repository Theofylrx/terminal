import { APIRequestContext, request, APIResponse } from '@playwright/test';
import config from '../../config/config';

/**
 * API Client Response Interface
 */
export interface ApiResponse<T = any> {
  status: number;
  statusText: string;
  headers: Record<string, string>;
  body: T;
  ok: boolean;
  raw: APIResponse;
}

/**
 * API Client wrapper for Terminal Trading System
 *
 * Provides reusable methods for HTTP operations with:
 * - Automatic JWT token management
 * - Built-in error handling
 * - Response parsing
 * - Retry logic
 */
export class ApiClient {
  private requestContext: APIRequestContext | null = null;
  private baseURL: string;
  private defaultHeaders: Record<string, string>;
  private authToken: string | null = null;

  constructor(baseURL: string = config.apiBaseUrl, headers: Record<string, string> = {}) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...headers,
    };
  }

  /**
   * Initialize the API request context
   */
  async init(): Promise<void> {
    this.requestContext = await request.newContext({
      baseURL: this.baseURL,
      extraHTTPHeaders: this.defaultHeaders,
      timeout: config.timeouts.apiRequest,
    });
  }

  /**
   * Dispose of the request context
   */
  async dispose(): Promise<void> {
    if (this.requestContext) {
      await this.requestContext.dispose();
      this.requestContext = null;
    }
  }

  /**
   * Set authentication token (JWT)
   */
  setAuthToken(token: string): void {
    this.authToken = token;
    this.defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  /**
   * Remove authentication token
   */
  removeAuthToken(): void {
    this.authToken = null;
    delete this.defaultHeaders['Authorization'];
  }

  /**
   * Get current auth token
   */
  getAuthToken(): string | null {
    return this.authToken;
  }

  /**
   * GET request
   */
  async get<T = any>(
    endpoint: string,
    options: { params?: Record<string, any>, headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const response = await this.requestContext!.get(endpoint, {
      params: options.params,
      headers: { ...this.defaultHeaders, ...options.headers },
    });

    return await this.buildResponse<T>(response);
  }

  /**
   * POST request
   */
  async post<T = any>(
    endpoint: string,
    data: any,
    options: { headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const response = await this.requestContext!.post(endpoint, {
      data,
      headers: { ...this.defaultHeaders, ...options.headers },
    });

    return await this.buildResponse<T>(response);
  }

  /**
   * PUT request
   */
  async put<T = any>(
    endpoint: string,
    data: any,
    options: { headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const response = await this.requestContext!.put(endpoint, {
      data,
      headers: { ...this.defaultHeaders, ...options.headers },
    });

    return await this.buildResponse<T>(response);
  }

  /**
   * PATCH request
   */
  async patch<T = any>(
    endpoint: string,
    data: any,
    options: { headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const response = await this.requestContext!.patch(endpoint, {
      data,
      headers: { ...this.defaultHeaders, ...options.headers },
    });

    return await this.buildResponse<T>(response);
  }

  /**
   * DELETE request
   */
  async delete<T = any>(
    endpoint: string,
    options: { headers?: Record<string, string> } = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const response = await this.requestContext!.delete(endpoint, {
      headers: { ...this.defaultHeaders, ...options.headers },
    });

    return await this.buildResponse<T>(response);
  }

  /**
   * Build standardized response object
   */
  private async buildResponse<T>(response: APIResponse): Promise<ApiResponse<T>> {
    return {
      status: response.status(),
      statusText: response.statusText(),
      headers: response.headers(),
      body: await this.parseResponse<T>(response),
      ok: response.ok(),
      raw: response,
    };
  }

  /**
   * Parse response body based on content type
   */
  private async parseResponse<T>(response: APIResponse): Promise<T> {
    const contentType = response.headers()['content-type'] || '';

    if (contentType.includes('application/json')) {
      try {
        return await response.json() as T;
      } catch (error) {
        // If JSON parsing fails, return text
        return await response.text() as unknown as T;
      }
    }

    return await response.text() as unknown as T;
  }

  /**
   * Ensure request context is initialized
   */
  private ensureInitialized(): void {
    if (!this.requestContext) {
      throw new Error('API Client not initialized. Call init() first.');
    }
  }

  /**
   * Retry request with exponential backoff
   */
  async retryRequest<T = any>(
    requestFn: () => Promise<ApiResponse<T>>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<ApiResponse<T>> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        return await requestFn();
      } catch (error) {
        lastError = error as Error;
        if (attempt < maxRetries - 1) {
          const delay = baseDelay * Math.pow(2, attempt);
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    throw new Error(`Request failed after ${maxRetries} attempts: ${lastError?.message}`);
  }

  /**
   * Upload file (multipart/form-data)
   */
  async uploadFile<T = any>(
    endpoint: string,
    filePath: string,
    fieldName: string = 'file',
    additionalData: Record<string, any> = {}
  ): Promise<ApiResponse<T>> {
    this.ensureInitialized();

    const formData = {
      [fieldName]: filePath,
      ...additionalData,
    };

    const response = await this.requestContext!.post(endpoint, {
      multipart: formData,
      headers: {
        ...this.defaultHeaders,
        'Content-Type': 'multipart/form-data',
      },
    });

    return await this.buildResponse<T>(response);
  }
}
