'use server'
import { redirect } from 'next/navigation'
import * as z from "zod";
import { createSession, deleteSession } from '@/src/lib/session'
import { postLogin } from '@/src/service/auth.dal'
import { loginInputSchema, validateLoginPayload } from '@/src/lib/auth-helpers'

export type LoginActionState = {
  error: string | null
  errors: unknown
}

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

export async function logout() {
  await deleteSession()
  redirect('/login')
}