// lib/auth.ts — JWT helpers for Phase II auth
// Uses `jose` (edge-compatible) for sign/verify.
// Session stored in an httpOnly cookie.

import { SignJWT, jwtVerify } from 'jose'
import { cookies } from 'next/headers'

const SECRET = new TextEncoder().encode(
  process.env.BETTER_AUTH_SECRET ?? 'dev-secret-change-in-production'
)

export const COOKIE_NAME = 'auth_token'
const EXPIRY = '7d'

export interface SessionUser {
  sub: string   // user id
  email: string
  name: string
}

export async function signToken(payload: SessionUser): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime(EXPIRY)
    .sign(SECRET)
}

export async function verifyToken(token: string): Promise<SessionUser | null> {
  try {
    const { payload } = await jwtVerify(token, SECRET)
    return payload as unknown as SessionUser
  } catch {
    return null
  }
}

/** Returns the decoded session or null (reads from httpOnly cookie). */
export async function getSession(): Promise<SessionUser | null> {
  const cookieStore = await cookies()
  const token = cookieStore.get(COOKIE_NAME)?.value
  if (!token) return null
  return verifyToken(token)
}

/** Returns the raw JWT string for passing to client components as a prop. */
export async function getToken(): Promise<string | null> {
  const cookieStore = await cookies()
  return cookieStore.get(COOKIE_NAME)?.value ?? null
}
