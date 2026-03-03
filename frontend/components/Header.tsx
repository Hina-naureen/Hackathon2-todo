'use client'

import { signOut } from '@/app/actions'
import { useLanguage } from '@/lib/i18n'

interface Props {
  userEmail: string
  userName: string
}

export default function Header({ userEmail, userName }: Props) {
  const { lang, setLang, t } = useLanguage()

  return (
    <header className="bg-white border-b border-gray-100 shadow-sm dark:bg-zinc-900 dark:border-zinc-800">
      <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
        <span className="font-semibold tracking-tight text-slate-900 dark:text-white">
          {t('appName')}
        </span>

        <div className="flex items-center gap-3">
          {/* Language Toggle */}
          <button
            onClick={() => setLang(lang === 'en' ? 'ur' : 'en')}
            title="Toggle Language / زبان تبدیل کریں"
            className="flex items-center gap-1 text-xs font-semibold px-2.5 py-1.5 rounded-lg border border-violet-200 text-violet-700 hover:bg-violet-50 transition-colors dark:border-violet-700 dark:text-violet-400 dark:hover:bg-violet-900/20"
          >
            🌐 {t('language')}
          </button>

          <span className="text-sm text-slate-500 dark:text-zinc-400" title={userName}>
            {userEmail}
          </span>

          <form action={signOut}>
            <button
              type="submit"
              className="text-sm text-slate-600 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-slate-50 hover:text-slate-900 transition-colors dark:text-zinc-400 dark:border-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-white"
            >
              {t('signOut')}
            </button>
          </form>
        </div>
      </div>
    </header>
  )
}
