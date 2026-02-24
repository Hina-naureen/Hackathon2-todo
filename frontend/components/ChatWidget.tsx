'use client'

import { useState } from 'react'
import ChatPanel from './ChatPanel'

// ---------------------------------------------------------------------------
// ChatWidget — floating button + panel, fixed bottom-right
// ---------------------------------------------------------------------------

interface ChatWidgetProps {
  token: string
}

export default function ChatWidget({ token }: ChatWidgetProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

      {/* Chat panel — CSS transition for smooth enter/exit (no external deps) */}
      <div
        className={`transition-all duration-200 ease-out origin-bottom-right ${
          open
            ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 scale-95 translate-y-2 pointer-events-none'
        }`}
      >
        <ChatPanel token={token} onClose={() => setOpen(false)} />
      </div>

      {/* Floating toggle button */}
      <button
        onClick={() => setOpen(prev => !prev)}
        aria-label={open ? 'Close AI chat' : 'Open AI chat'}
        className={`
          relative w-14 h-14 rounded-2xl shadow-xl
          backdrop-blur-md border border-white/20
          flex items-center justify-center
          transition-all duration-200 ease-out
          hover:scale-110 hover:shadow-2xl active:scale-95
          ${open
            ? 'bg-slate-700/90 text-white dark:bg-zinc-700/90'
            : 'bg-slate-900/90 text-white dark:bg-zinc-800/90 dark:border-zinc-700/60'
          }
        `}
      >
        {open ? (
          /* Close — X icon */
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        ) : (
          /* Open — chat bubble icon */
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        )}

        {/* AI availability indicator — pulsing green dot */}
        {!open && (
          <span
            aria-label="AI available"
            className="absolute -top-1 -right-1 w-3.5 h-3.5 rounded-full bg-emerald-400 border-2 border-white dark:border-zinc-900 animate-pulse"
          />
        )}
      </button>
    </div>
  )
}
