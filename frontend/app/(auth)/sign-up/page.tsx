'use client'

import { useActionState } from 'react'
import Link from 'next/link'
import { signUp } from '@/app/actions'

export default function SignUpPage() {
  const [error, formAction, isPending] = useActionState(signUp, null)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 px-4 dark:bg-zinc-900">
      <p className="text-xs font-medium tracking-widest text-slate-400 uppercase mb-3 dark:text-zinc-500">
        Evolution of Todo
      </p>
      <h1 className="text-2xl font-semibold tracking-tight text-slate-900 mb-8 dark:text-white">
        Create an account
      </h1>

      <div className="w-full max-w-sm bg-white rounded-2xl border border-gray-100 shadow-sm p-8 dark:bg-zinc-800 dark:border-zinc-700">
        <form action={formAction} className="flex flex-col gap-4">
          <div>
            <label htmlFor="name" className="block text-xs font-medium text-slate-600 mb-1.5 dark:text-zinc-400">
              Name
            </label>
            <input
              id="name"
              name="name"
              type="text"
              required
              autoComplete="name"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
              placeholder="Alice"
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-xs font-medium text-slate-600 mb-1.5 dark:text-zinc-400">
              Email
            </label>
            <input
              id="email"
              name="email"
              type="email"
              required
              autoComplete="email"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-xs font-medium text-slate-600 mb-1.5 dark:text-zinc-400">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
              placeholder="••••••••"
            />
            <p className="text-xs text-slate-400 mt-1.5 dark:text-zinc-500">At least 8 characters</p>
          </div>

          {error && (
            <p className="text-xs text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full bg-slate-900 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-slate-700 disabled:opacity-50 transition-colors mt-1 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          >
            {isPending ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-xs text-slate-500 text-center mt-6 dark:text-zinc-400">
          Already have an account?{' '}
          <Link href="/sign-in" className="text-slate-900 font-medium hover:underline dark:text-white">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
