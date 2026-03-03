// middleware.ts — route protection (Next.js App Router middleware convention)
// Runs at the edge; checks cookie existence only (JWT verified at page level).
//
// Routing rules:
//   /tasks (and sub-paths) → redirect to /sign-in if unauthenticated
//   /sign-in, /sign-up     → redirect to /tasks  if already authenticated
//   /                      → redirect to /tasks or /sign-in

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const authed = !!request.cookies.get('auth_token')?.value

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
