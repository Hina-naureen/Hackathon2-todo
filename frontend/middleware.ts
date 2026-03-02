// middleware.ts — route protection (Next.js App Router middleware convention)
// Runs at the edge; uses `jose` (edge-compatible) to verify the auth cookie.
//
// Routing rules:
//   /tasks (and sub-paths) → redirect to /sign-in if unauthenticated
//   /sign-in, /sign-up     → redirect to /tasks  if already authenticated
//   /                      → redirect to /tasks or /sign-in

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { jwtVerify } from 'jose'

const SECRET = new TextEncoder().encode(
  process.env.BETTER_AUTH_SECRET ?? 'dev-secret-change-in-production'
)

async function isAuthenticated(request: NextRequest): Promise<boolean> {
  const token = request.cookies.get('auth_token')?.value
  if (!token) return false
  try {
    await jwtVerify(token, SECRET)
    return true
  } catch {
    return false
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const authed = await isAuthenticated(request)

  // Protected routes
  if (pathname.startsWith('/tasks')) {
    if (!authed) {
      return NextResponse.redirect(new URL('/sign-in', request.url))
    }
  }

  // Auth routes — redirect away if already logged in
  if (pathname === '/sign-in' || pathname === '/sign-up') {
    if (authed) {
      return NextResponse.redirect(new URL('/tasks', request.url))
    }
  }

  // Root — always redirect
  if (pathname === '/') {
    return NextResponse.redirect(new URL(authed ? '/tasks' : '/sign-in', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/', '/sign-in', '/sign-up', '/tasks/:path*'],
}
