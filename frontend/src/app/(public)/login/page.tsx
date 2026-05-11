'use client'
import { useActionState } from 'react'
import { useRouter } from 'next/router'
import { loginUser } from '@/src/actions/auth.action'

const initialState = {
  message: '',
}

export default function LoginPage() {
  const router = useRouter()
  const [state, formAction, pending] = useActionState(loginUser, initialState)

  return (
    <form onSubmit={formAction}>
      <input type="email" name="email" placeholder="Email" required />
      <input type="password" name="password" placeholder="Password" required />
      <button type="submit" disabled={pending}>Login</button>
    </form>
  )
}