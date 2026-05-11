/**
 * Enhanced type definitions for API response handling
 *
 * Problem: The current code uses result.data.data?.email which is confusing
 * because it accesses two nested "data" properties (the envelope and payload).
 *
 * Solution: Provide helper types and functions that make the structure explicit
 * and type-safe, preventing future bugs.
 */

import type { z } from 'zod/v4'
import type { ServiceResult } from './type.lib'
import {
  authenticationLogin200Schema,
  type accessTokenDataSchema,
} from '@/src/models/gen'

/**
 * Type: LoginResponse (the API response envelope)
 *
 * This is what gets returned from postLogin() as ServiceResult<LoginResponse>
 * Structure:
 * - success: boolean - indicates success at the API level
 * - status: number - HTTP-like status code from API
 * - message: string - human-readable message
 * - data: AccessTokenData | null - the actual login payload
 * - error: ApiError | null - error details if failed
 */
export type LoginResponse = z.infer<typeof authenticationLogin200Schema>

/**
 * Type: AccessTokenData (the API response payload)
 *
 * This is what gets nested inside LoginResponse.data
 * Structure:
 * - access_token: string - JWT or session token
 * - token_type: string - typically "Bearer"
 * - email: string - user's email address
 */
export type AccessTokenData = z.infer<typeof accessTokenDataSchema>

/**
 * Type: LoginSuccess (with proper typing)
 *
 * When ServiceResult.ok is true, we know:
 * - ServiceResult.data (envelope) is LoginResponse
 * - ServiceResult.data.data (payload) is AccessTokenData
 */
export type LoginSuccess = ServiceResult<LoginResponse> & { ok: true }

/**
 * Helper: Extract AccessTokenData safely from ServiceResult
 *
 * This function makes the nested property access explicit and type-safe.
 * Instead of directly using result.data.data?.email, use:
 * const payload = getLoginPayload(result);
 * const email = payload?.email;
 *
 * @param result - The ServiceResult from postLogin()
 * @returns AccessTokenData | null if successful, null if failed
 */
export function getLoginPayload(result: ServiceResult<LoginResponse>): AccessTokenData | null {
  if (!result.ok) {
    return null
  }

  return result.data.data ?? null
}

/**
 * Helper: Extract user email safely from login result
 *
 * Provides a single function for the common operation of getting the email.
 * Handles all edge cases (failed request, null payload, etc.)
 *
 * @param result - The ServiceResult from postLogin()
 * @returns User email if available, empty string otherwise
 */
export function getLoginEmail(result: ServiceResult<LoginResponse>): string {
  const payload = getLoginPayload(result)
  return payload?.email ?? ''
}

/**
 * Type Guard: Check if result is a successful login
 *
 * Use this to narrow ServiceResult to LoginSuccess type
 * @param result - The ServiceResult to check
 * @returns true if login succeeded
 */
export function isLoginSuccess(result: ServiceResult<LoginResponse>): result is LoginSuccess {
  return result.ok
}

/**
 * Helper: Validate and extract AccessTokenData
 *
 * This function adds runtime validation that the payload has
 * all required fields (especially email).
 *
 * @param result - The ServiceResult from postLogin()
 * @returns email if all validations pass, null otherwise
 */
export function validateLoginPayload(result: ServiceResult<LoginResponse>): string | null {
  const payload = getLoginPayload(result)

  if (!payload) {
    return null
  }

  // Validate required fields
  if (!payload.access_token || typeof payload.access_token !== 'string') {
    console.error('Invalid login payload: missing or invalid access_token')
    return null
  }

  if (!payload.token_type || typeof payload.token_type !== 'string') {
    console.error('Invalid login payload: missing or invalid token_type')
    return null
  }

  if (!payload.email || typeof payload.email !== 'string') {
    console.error('Invalid login payload: missing or invalid email')
    return null
  }

  // Validate email format
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(payload.email)) {
    console.error('Invalid login payload: email format invalid')
    return null
  }

  return payload.email
}
