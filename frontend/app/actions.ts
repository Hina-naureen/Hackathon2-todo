'use server'

// app/actions.ts — server actions for authentication
// Calls FastAPI backend for sign-in / sign-up.
// On success, stores the backend-issued JWT in an httpOnly cookie.

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { COOKIE_NAME } from '@/lib/auth'

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: process.env.NODE_ENV === 'production',
  sameSite: 'lax' as const,
  maxAge: 60 * 60 * 24 * 7, // 7 days
  path: '/',
}

export async function signIn(
  _prevState: string | null,
  formData: FormData
): Promise<string | null> {
  const email = (formData.get('email') as string | null) ?? ''
  const password = (formData.get('password') as string | null) ?? ''

  let res: Response
  try {
    res = await fetch(`${API_URL}/api/auth/sign-in`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
  } catch {
    return 'Could not reach the server. Please try again.'
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({})) as { detail?: string }
    return data.detail ?? 'Invalid email or password.'
  }

  const { token } = await res.json() as { token: string }
  const cookieStore = await cookies()
  cookieStore.set(COOKIE_NAME, token, COOKIE_OPTIONS)

  redirect('/tasks')
}

export async function signUp(
  _prevState: string | null,
  formData: FormData
): Promise<string | null> {
  const name = (formData.get('name') as string | null)?.trim() ?? ''
  const email = (formData.get('email') as string | null)?.trim() ?? ''
  const password = (formData.get('password') as string | null) ?? ''

  if (!name) return 'Name is required.'
  if (!email) return 'Email is required.'
  if (password.length < 8) return 'Password must be at least 8 characters.'

  let res: Response
  try {
    res = await fetch(`${API_URL}/api/auth/sign-up`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    })
  } catch {
    return 'Could not reach the server. Please try again.'
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({})) as { detail?: string }
    return data.detail ?? 'Failed to create account.'
  }

  const { token } = await res.json() as { token: string }
  const cookieStore = await cookies()
  cookieStore.set(COOKIE_NAME, token, COOKIE_OPTIONS)

  redirect('/tasks')
}

export async function signOut(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(COOKIE_NAME)
  redirect('/sign-in')
}
