

import { z } from 'zod/v4'
import type { ServiceResult } from './type.lib'
import { authenticationLogin200Schema, loginRequestSchema } from '@/src/models/gen'

export const loginInputSchema = loginRequestSchema.extend({
  email: z.email({ error: 'Email must be valid' }),
  password: z.string().min(1, { error: 'Password is required' }),
})

export type LoginInput = z.infer<typeof loginInputSchema>
export type LoginResponse = z.infer<typeof authenticationLogin200Schema>

/**
 * Extracts the login response data from a service result.
 * @param result - The service result containing the login response.
 * @returns The extracted login response data, or null if the result is not OK or data is missing.
 */
export function getLoginPayload(
  result: ServiceResult<LoginResponse>,
): LoginResponse['data'] | null {
  if (!result.ok) {
    return null
  }
  return result.data.data ?? null
}

/**
 * Validates the login payload and extracts the email.
 * @param result - The service result containing the login response.
 * @returns The email string if valid and present, otherwise null.
 */
export function validateLoginPayload(
  result: ServiceResult<LoginResponse>,
): string | null {
  const payload = getLoginPayload(result)
  if (!payload || typeof payload.email !== 'string' || payload.email.length === 0) {
    return null
  }
  return payload.email
}