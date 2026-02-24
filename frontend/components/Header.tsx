'use client'

import { signOut } from '@/app/actions'

interface Props {
  userEmail: string
  userName: string
}

export default function Header({ userEmail, userName }: Props) {
  return (
    <header className="bg-white border-b border-gray-100 shadow-sm dark:bg-zinc-900 dark:border-zinc-800">
      <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
        <span className="font-semibold tracking-tight text-slate-900 dark:text-white">
          Evolution of Todo
        </span>

        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500 dark:text-zinc-400" title={userName}>
            {userEmail}
          </span>
          <form action={signOut}>
            <button
              type="submit"
              className="text-sm text-slate-600 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 hover:text-slate-900 transition-colors dark:text-zinc-400 dark:border-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-white"
            >
              Sign out
            </button>
          </form>
        </div>
      </div>
    </header>
  )
}
