'use server'
import { redirect } from 'next/navigation'
import * as z from "zod";
import { createSession, deleteSession } from '@/src/lib/session'
import { postLogin } from '@/src/service/auth.dal'
import { loginInputSchema, validateLoginPayload } from '@/src/lib/auth-helpers'

/**
 * Represents the state of a login action, including any errors encountered.
 */
export type LoginActionState = {
  /**
   * A human-readable error message, or null if no error occurred.
   */
  error: string | null
  /**
   * Detailed error information, potentially containing Zod validation errors.
   */
  errors: unknown
}

/**
 * Handles the login logic for a user.
 *
 * This function validates the provided email and password, attempts to authenticate
 * the user via the `postLogin` service, creates a session if authentication is
 * successful, and redirects the user to the home page.
 *
 * @param _initialState - The initial state of the login action, not used internally.
 * @param formData - The form data submitted by the user, containing email and password.
 * @returns A Promise resolving to the `LoginActionState` after processing.
 */
export async function loginUser(_initialState: LoginActionState, formData: FormData): Promise<LoginActionState> {
  const rawEmail = formData.get('email')
  const rawPassword = formData.get('password')
  const validatedFields = loginInputSchema.safeParse({
    email: typeof rawEmail === 'string' ? rawEmail.trim().toLowerCase() : '',
    password: typeof rawPassword === 'string' ? rawPassword : '',
  })

  if (!validatedFields.success) {
    return {
      error: null,
      errors: z.treeifyError(validatedFields.error),
    }
  }

  const result = await postLogin(validatedFields.data.email, validatedFields.data.password)

  if (!result.ok) {
    return {
      error: result.error.userMessage,
      errors: null,
    }
  }

  // Extract email safely with validation
  const email = validateLoginPayload(result)
  if (!email) {
    return {
      error: 'Invalid response from server',
      errors: null,
    }
  }

  await createSession(email)
  redirect('/')

  return { error: null, errors: null }
}

/**
 * Handles the logout logic for a user.
 *
 * This function deletes the current user's session and redirects them to the
 * login page.
 *
 * @returns A Promise resolving once the session is deleted and the redirect is issued.
 */
export async function logout() {
  await deleteSession()
  redirect('/login')
}