'use server'
import { redirect } from 'next/navigation'
import * as z from "zod";
import { createSession, deleteSession } from '@/src/lib/session'
import { postLogin } from '@/src/service/auth.dal'
import { validateLoginPayload } from '@/src/lib/auth.helpers'

const schema = z.object({
  email: z.string().email('Email must be valid'),
  password: z.string().min(1, 'Password is required')
})

export async function loginUser(initialState: unknown, formData: FormData) {
  const validatedFields = schema.safeParse({
    email: formData.get('email'),
    password: formData.get('password')
  })

  if (!validatedFields.success) {
    return {
      errors: z.treeifyError(validatedFields.error),
    }
  }

  const result = await postLogin(validatedFields.data.email, validatedFields.data.password)

  if (!result.ok) {
    return {
      error: result.error.userMessage,
    }
  }

  // Extract email safely with validation
  const email = validateLoginPayload(result)
  if (!email) {
    return {
      error: 'Invalid response from server',
    }
  }

  await createSession(email)
  redirect('/')
}

export async function logout() {
  await deleteSession()
  redirect('/login')
}