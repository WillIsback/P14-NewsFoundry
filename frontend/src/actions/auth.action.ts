'use server'
import { createSession } from '@/src/lib/session'

import * as z from "zod";

const schema = z.object({
  email: z.string({
    error: 'Invalid Email',
  }),
  password: z.string({
    error: 'Invalid Password'
  })
})

export async function loginUser(initialState: any, formData: FormData) {
  const validatedFields = schema.safeParse({
    email: formData.get('email'),
    password: formData.get('password')
  })

  // Return early if the form data is invalid
  if (!validatedFields.success) {
    return {
      errors: z.treeifyError(validatedFields.error),
    }
  }
  console.log("Login server Action data : ",validatedFields.data)
  // Mutate data
}

export async function logout() {
  await deleteSession()
  redirect('/login')
}