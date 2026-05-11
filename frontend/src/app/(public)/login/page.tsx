'use client'
import { useActionState } from 'react'
import { useFormStatus } from 'react-dom'
import { LoaderCircle } from 'lucide-react'
import { loginUser } from '@/src/actions/auth.action'
import type { LoginActionState } from '@/src/actions/auth.action'

const initialState: LoginActionState = {
  error: null,
  errors: null,
}

function SubmitButton() {
  const { pending } = useFormStatus()

  return (
    <button type="submit" disabled={pending} className="inline-flex items-center gap-2">
      {pending ? <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
      {pending ? 'Signing in...' : 'Login'}
    </button>
  )
}

export default function LoginPage() {
  const [state, formAction] = useActionState(loginUser, initialState)

  return (
    <form action={formAction} className="space-y-3">
      <input type="email" name="email" placeholder="Email" required />
      <input type="password" name="password" placeholder="Password" required />
      {state?.error ? (
        <p role="status" aria-live="polite" className="text-sm text-red-600">
          {state.error}
        </p>
      ) : null}
      <SubmitButton />
    </form>
  )
}