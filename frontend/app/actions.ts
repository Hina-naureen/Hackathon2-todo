'use server'

// app/actions.ts — server actions for authentication
// signIn / signUp write an httpOnly JWT cookie on success.
// signOut clears it.

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { signToken, COOKIE_NAME } from '@/lib/auth'
import { findUserByEmail, createUser, verifyPassword } from '@/lib/user-store'

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

  const user = await findUserByEmail(email)
  if (!user || !(await verifyPassword(password, user.passwordHash))) {
    return 'Invalid email or password.'
  }

  const token = await signToken({ sub: user.id, email: user.email, name: user.name })
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

  const existing = await findUserByEmail(email)
  if (existing) return 'An account with this email already exists.'

  const user = await createUser({ name, email, password })
  const token = await signToken({ sub: user.id, email: user.email, name: user.name })
  const cookieStore = await cookies()
  cookieStore.set(COOKIE_NAME, token, COOKIE_OPTIONS)

  redirect('/tasks')
}

export async function signOut(): Promise<void> {
  const cookieStore = await cookies()
  cookieStore.delete(COOKIE_NAME)
  redirect('/sign-in')
}
