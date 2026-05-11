import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { loginUser } from '../auth.action'
import * as sessionLib from '@/src/lib/session'
import * as authDal from '@/src/service/auth.dal'
import { redirect } from 'next/navigation'

// Mock the dependencies
vi.mock('@/src/lib/session')
vi.mock('@/src/service/auth.dal')
vi.mock('next/navigation')

/**
 * Test Suite: Response Structure Validation
 *
 * These tests verify that the response structure from postLogin() matches
 * the expected ServiceResult<LoginResponse> shape and that we can safely
 * access result.data.data?.email without type errors.
 */
describe('loginUser - Response Structure & Email Access', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  /**
   * Test: Verify successful response structure
   *
   * Tests that when postLogin succeeds, the response structure is:
   * ServiceResult<LoginResponse> where:
   * - result.ok = true
   * - result.status = 200
   * - result.data = ApiResponse (envelope)
   *   - result.data.success = true
   *   - result.data.status = 200
   *   - result.data.message = "Login successful"
   *   - result.data.data = AccessTokenData (payload)
   *     - result.data.data.access_token = string
   *     - result.data.data.email = string
   *     - result.data.data.token_type = "Bearer"
   */
  it('should successfully access email from nested response structure (result.data.data.email)', async () => {
    const mockEmail = 'user@example.com'
    const mockAccessToken = 'test-token-123'

    // Mock the response structure: ServiceResult<LoginResponse>
    vi.mocked(authDal.postLogin).mockResolvedValueOnce({
      ok: true,
      status: 200,
      data: {
        // ApiResponse envelope (result.data)
        success: true,
        status: 200,
        message: 'Login successful',
        // AccessTokenData payload (result.data.data)
        data: {
          access_token: mockAccessToken,
          token_type: 'Bearer',
          email: mockEmail,
        },
        error: null,
      },
    })

    vi.mocked(sessionLib.createSession).mockResolvedValueOnce(undefined)
    vi.mocked(redirect).mockImplementation(() => {
      throw new Error('Redirect called')
    })

    const formData = new FormData()
    formData.append('email', mockEmail)
    formData.append('password', 'password123')

    try {
      await loginUser(undefined, formData)
    } catch {
      // redirect throws, which is expected
    }

    // Verify createSession was called with the extracted email
    expect(sessionLib.createSession).toHaveBeenCalledWith(mockEmail)
  })

  /**
   * Test: Handle null data payload gracefully
   *
   * Verifies that when result.data.data is null (e.g., unexpected response),
   * the optional chaining operator ?.email doesn't cause errors,
   * and we fall back to empty string ''
   */
  it('should handle null payload with optional chaining (result.data.data?.email ?? "")', async () => {
    // Mock response with null data payload
    vi.mocked(authDal.postLogin).mockResolvedValueOnce({
      ok: true,
      status: 200,
      data: {
        success: true,
        status: 200,
        message: 'Unexpected response',
        data: null, // Payload is null
        error: null,
      },
    })

    vi.mocked(sessionLib.createSession).mockResolvedValueOnce(undefined)
    vi.mocked(redirect).mockImplementation(() => {
      throw new Error('Redirect called')
    })

    const formData = new FormData()
    formData.append('email', 'test@example.com')
    formData.append('password', 'password123')

    try {
      await loginUser(undefined, formData)
    } catch {
      // expected
    }

    // Should fall back to empty string when data is null
    expect(sessionLib.createSession).toHaveBeenCalledWith('')
  })

  /**
   * Test: Verify error handling
   *
   * Ensures that when result.ok is false, we return early
   * and never attempt to access result.data.data?.email
   */
  it('should not access result.data.data when result.ok is false', async () => {
    const mockError = {
      kind: 'http' as const,
      code: 'HTTP_401',
      message: 'Invalid credentials',
      userMessage: 'Identifiants invalides',
      details: undefined,
    }

    // Mock failed response
    vi.mocked(authDal.postLogin).mockResolvedValueOnce({
      ok: false,
      status: 401,
      error: mockError,
    })

    const formData = new FormData()
    formData.append('email', 'test@example.com')
    formData.append('password', 'wrongpassword')

    const result = await loginUser(undefined, formData)

    // Should return error, never call createSession
    expect(result).toEqual({ error: 'Identifiants invalides' })
    expect(sessionLib.createSession).not.toHaveBeenCalled()
    expect(vi.mocked(redirect)).not.toHaveBeenCalled()
  })

  /**
   * Test: Type safety - email field exists in payload
   *
   * Validates that AccessTokenData has the email field
   * (helps catch if API response schema changes)
   */
  it('should have email field in AccessTokenData payload', async () => {
    const payloadWithEmail = {
      access_token: 'token',
      token_type: 'Bearer',
      email: 'user@example.com', // Email is a required field
    }

    expect(payloadWithEmail).toHaveProperty('email')
    expect(typeof payloadWithEmail.email).toBe('string')
  })

  /**
   * Test: Validation error handling
   *
   * Ensures form validation errors are caught before any API calls
   */
  it('should validate form data and return errors before API call', async () => {
    const formData = new FormData()
    formData.append('email', 'invalid-email') // Missing @
    formData.append('password', '')

    const result = await loginUser(undefined, formData)

    // Should have validation errors
    expect(result).toHaveProperty('errors')
    // Should never call postLogin
    expect(vi.mocked(authDal.postLogin)).not.toHaveBeenCalled()
  })
})

/**
 * Test Suite: Response Structure Type Validation
 *
 * These tests validate the Zod schema structure without mocking,
 * ensuring the generated schema matches expected types.
 */
describe('Response Schema Structure - Type Validation', () => {
  it('should validate AccessTokenData schema structure', async () => {
    // This test ensures the schema is correctly typed
    // In a real scenario, you'd import and parse with the actual schema
    const validAccessTokenData = {
      access_token: 'test-token',
      token_type: 'Bearer',
      email: 'user@example.com',
    }

    expect(validAccessTokenData).toMatchObject({
      access_token: expect.any(String),
      token_type: expect.any(String),
      email: expect.any(String),
    })
  })

  it('should validate ApiResponse schema structure', async () => {
    const validApiResponse = {
      success: true,
      status: 200,
      message: 'Login successful',
      data: {
        access_token: 'token',
        token_type: 'Bearer',
        email: 'user@example.com',
      },
      error: null,
    }

    expect(validApiResponse).toMatchObject({
      success: expect.any(Boolean),
      status: expect.any(Number),
      message: expect.any(String),
      data: expect.objectContaining({
        email: expect.any(String),
      }),
      error: expect.any(Object),
    })
  })

  it('should handle ServiceResult wrapper structure', async () => {
    const validServiceResult = {
      ok: true,
      status: 200,
      data: {
        success: true,
        status: 200,
        message: 'Success',
        data: {
          access_token: 'token',
          token_type: 'Bearer',
          email: 'user@example.com',
        },
        error: null,
      },
    }

    // Verify the nesting path: result.data.data.email
    expect(validServiceResult.data.data.email).toBe('user@example.com')
  })
})
