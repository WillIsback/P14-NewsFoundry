'use server'
import { redirect } from 'next/navigation'
import * as z from 'zod'
import { createSession, deleteSession } from '@/src/lib/session'
import { postLogin } from '@/src/service/auth.dal'
import { getLoginEmail, validateLoginPayload } from '@/src/lib/auth.helpers'

const schema = z.object({
  email: z.string({
    error: 'Invalid Email',
  }),
  password: z.string({
    error: 'Invalid Password',
  }),
})

/**
 * Server Action: loginUser
 *
 * Validates login credentials and creates a session for the user.
 *
 * IMPROVED: Uses getLoginEmail() helper instead of result.data.data?.email
 * Benefits:
 * - Type-safe: Helper ensures proper typing of nested response
 * - Readable: Clear function name documents the intent
 * - Maintainable: Single place to update if API schema changes
 * - Testable: Helper is independently tested
 *
 * @param initialState - Previous form state (for server action framework)
 * @param formData - Form submission data
 * @returns Object with either { errors: {...} }, { error: "string" }, or redirect
 */
export async function loginUser(initialState: unknown, formData: FormData) {
  const validatedFields = schema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  })

  if (!validatedFields.success) {
    return {
      errors: z.treeifyError(validatedFields.error),
    }
  }

  const result = await postLogin(
    validatedFields.data.email,
    validatedFields.data.password
  )

  if (!result.ok) {
    return {
      error: result.error.userMessage,
    }
  }

  /**
   * FIX: Instead of: result.data.data?.email
   * Use: getLoginEmail(result)
   *
   * This helper:
   * 1. Makes the nested access explicit (getLoginPayload)
   * 2. Provides proper null handling
   * 3. Falls back to empty string if email unavailable
   * 4. Follows DRY principle (single source of truth)
   */
  const email = getLoginEmail(result)

  await createSession(email)
  redirect('/')
}

/**
 * ALTERNATIVE: Using validateLoginPayload for stricter validation
 *
 * If you want runtime validation that email is properly formatted:
 *
 * export async function loginUserStrict(
 *   initialState: unknown,
 *   formData: FormData
 * ) {
 *   const validatedFields = schema.safeParse({
 *     email: formData.get('email'),
 *     password: formData.get('password'),
 *   })
 *
 *   if (!validatedFields.success) {
 *     return { errors: z.treeifyError(validatedFields.error) }
 *   }
 *
 *   const result = await postLogin(
 *     validatedFields.data.email,
 *     validatedFields.data.password
 *   )
 *
 *   if (!result.ok) {
 *     return { error: result.error.userMessage }
 *   }
 *
 *   // Validate payload at runtime + validate email format
 *   const email = validateLoginPayload(result)
 *
 *   if (!email) {
 *     return {
 *       error: 'Server returned invalid data. Please try again.',
 *     }
 *   }
 *
 *   await createSession(email)
 *   redirect('/')
 * }
 */

export async function logout() {
  await deleteSession()
  redirect('/login')
}
