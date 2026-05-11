import { z } from 'zod/v4'
import type { ServiceResult } from './type.lib'
import { authenticationLogin200Schema, loginRequestSchema } from '@/src/models/gen'

export const loginInputSchema = loginRequestSchema.extend({
  email: z.email({ error: 'Email must be valid' }),
  password: z.string().min(1, { error: 'Password is required' }),
})

export type LoginInput = z.infer<typeof loginInputSchema>
export type LoginResponse = z.infer<typeof authenticationLogin200Schema>

export function getLoginPayload(
  result: ServiceResult<LoginResponse>,
): LoginResponse['data'] | null {
  if (!result.ok) {
    return null
  }
  return result.data.data ?? null
}

export function validateLoginPayload(
  result: ServiceResult<LoginResponse>,
): string | null {
  const payload = getLoginPayload(result)
  if (!payload || typeof payload.email !== 'string' || payload.email.length === 0) {
    return null
  }
  return payload.email
}
