'use server'
import { redirect } from 'next/navigation'
import * as z from "zod";
import { createSession, deleteSession } from '@/src/lib/session'
import { postLogin } from '@/src/service/auth.dal'

const schema = z.object({
  email: z.string({
    error: 'Invalid Email',
  }),
  password: z.string({
    error: 'Invalid Password'
  })
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

  await createSession(result.data.data?.email ?? '')
  redirect('/')
}

export async function logout() {
  await deleteSession()
  redirect('/login')
}