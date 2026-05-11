import { describe, it, expect } from 'vitest'
import {
  getLoginPayload,
  getLoginEmail,
  isLoginSuccess,
  validateLoginPayload,
  type LoginResponse,
  type LoginSuccess,
} from '../auth.helpers'
import type { ServiceResult } from '../type.lib'

/**
 * Test Suite: Auth Helper Functions
 *
 * These tests validate the helper functions that safely extract
 * and type the nested response structure.
 */
describe('Auth Helper Functions', () => {
  /**
   * Test: getLoginPayload extracts nested data safely
   */
  describe('getLoginPayload', () => {
    it('should extract AccessTokenData from successful result', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Login successful',
          data: {
            access_token: 'token-123',
            token_type: 'Bearer',
            email: 'user@example.com',
          },
          error: null,
        },
      }

      const payload = getLoginPayload(result)

      expect(payload).toBeDefined()
      expect(payload?.email).toBe('user@example.com')
      expect(payload?.access_token).toBe('token-123')
      expect(payload?.token_type).toBe('Bearer')
    })

    it('should return null when payload is null', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Unexpected response',
          data: null,
          error: null,
        },
      }

      const payload = getLoginPayload(result)

      expect(payload).toBeNull()
    })

    it('should return null when result.ok is false', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: false,
        status: 401,
        error: {
          kind: 'http',
          code: 'HTTP_401',
          message: 'Unauthorized',
          userMessage: 'Invalid credentials',
          details: undefined,
        },
      }

      const payload = getLoginPayload(result)

      expect(payload).toBeNull()
    })
  })

  /**
   * Test: getLoginEmail extracts email with fallback
   */
  describe('getLoginEmail', () => {
    it('should return email from successful result', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Login successful',
          data: {
            access_token: 'token',
            token_type: 'Bearer',
            email: 'john@example.com',
          },
          error: null,
        },
      }

      const email = getLoginEmail(result)

      expect(email).toBe('john@example.com')
    })

    it('should return empty string when payload is null', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Response',
          data: null,
          error: null,
        },
      }

      const email = getLoginEmail(result)

      expect(email).toBe('')
    })

    it('should return empty string when result failed', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: false,
        status: 401,
        error: {
          kind: 'http',
          code: 'HTTP_401',
          message: 'Unauthorized',
          userMessage: 'Invalid credentials',
          details: undefined,
        },
      }

      const email = getLoginEmail(result)

      expect(email).toBe('')
    })
  })

  /**
   * Test: isLoginSuccess type guard
   */
  describe('isLoginSuccess', () => {
    it('should return true for successful result', () => {
      const result: ServiceResult<LoginResponse> = {
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

      expect(isLoginSuccess(result)).toBe(true)
    })

    it('should return false for failed result', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: false,
        status: 401,
        error: {
          kind: 'http',
          code: 'HTTP_401',
          message: 'Unauthorized',
          userMessage: 'Invalid credentials',
          details: undefined,
        },
      }

      expect(isLoginSuccess(result)).toBe(false)
    })

    it('should narrow type in conditional', () => {
      const result: ServiceResult<LoginResponse> = {
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

      if (isLoginSuccess(result)) {
        // After type guard, result is typed as LoginSuccess
        // so we can safely access result.data.data
        const _payload = result.data.data
        expect(_payload).toBeDefined()
      }
    })
  })

  /**
   * Test: validateLoginPayload adds runtime validation
   */
  describe('validateLoginPayload', () => {
    it('should return email when all fields are valid', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Success',
          data: {
            access_token: 'token-abc123',
            token_type: 'Bearer',
            email: 'valid@example.com',
          },
          error: null,
        },
      }

      const email = validateLoginPayload(result)

      expect(email).toBe('valid@example.com')
    })

    it('should return null when access_token is missing', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Success',
          data: {
            access_token: '', // Invalid: empty
            token_type: 'Bearer',
            email: 'user@example.com',
          },
          error: null,
        },
      }

      const email = validateLoginPayload(result)

      expect(email).toBeNull()
    })

    it('should return null when email is missing', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Success',
          data: {
            access_token: 'token',
            token_type: 'Bearer',
            email: '', // Invalid: empty
          },
          error: null,
        },
      }

      const email = validateLoginPayload(result)

      expect(email).toBeNull()
    })

    it('should return null when email format is invalid', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Success',
          data: {
            access_token: 'token',
            token_type: 'Bearer',
            email: 'not-an-email', // Invalid: no @ symbol
          },
          error: null,
        },
      }

      const email = validateLoginPayload(result)

      expect(email).toBeNull()
    })

    it('should return null when payload is null', () => {
      const result: ServiceResult<LoginResponse> = {
        ok: true,
        status: 200,
        data: {
          success: true,
          status: 200,
          message: 'Success',
          data: null,
          error: null,
        },
      }

      const email = validateLoginPayload(result)

      expect(email).toBeNull()
    })
  })
})
