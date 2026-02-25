'use client'

import { useState } from 'react'
import ChatPanel from './ChatPanel'

// ---------------------------------------------------------------------------
// ChatWidget — floating button + panel, fixed bottom-right
// ---------------------------------------------------------------------------

interface ChatWidgetProps {
  token: string
  onMutation?: () => void
  pendingTaskCount: number
}

export default function ChatWidget({ token, onMutation, pendingTaskCount }: ChatWidgetProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

      {/* Chat panel — spring pop-in (cubic-bezier overshoot), scale-out exit */}
      <div
        className={`transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] origin-bottom-right ${
          open
            ? 'opacity-100 scale-100 translate-y-0 pointer-events-auto'
            : 'opacity-0 scale-90 translate-y-4 pointer-events-none'
        }`}
      >
        <ChatPanel
          token={token}
          onClose={() => setOpen(false)}
          onMutation={onMutation}
          pendingTaskCount={pendingTaskCount}
        />
      </div>

      {/* Floating toggle button */}
      <button
        onClick={() => setOpen(prev => !prev)}
        aria-label={open ? 'Close AI chat' : 'Open AI chat'}
        className={`
          relative w-14 h-14 rounded-2xl
          backdrop-blur-md
          flex items-center justify-center
          transition-all duration-200 ease-out
          active:scale-95
          ${open
            ? 'bg-slate-700/90 text-white border border-white/20 shadow-xl hover:shadow-2xl hover:scale-105 dark:bg-zinc-700/90 dark:border-zinc-600/40'
            : 'bg-slate-900/90 text-white border border-violet-500/30 ring-1 ring-violet-500/20 shadow-[0_4px_24px_rgba(139,92,246,0.28)] hover:shadow-[0_6px_32px_rgba(139,92,246,0.45)] hover:scale-110 dark:bg-zinc-800/90 dark:border-violet-500/25'
          }
        `}
      >
        {/* Icon crossfade: chat bubble ↔ X with spin */}
        <span
          className={`absolute transition-all duration-200 ${
            open ? 'opacity-100 rotate-0 scale-100' : 'opacity-0 rotate-45 scale-75'
          }`}
          aria-hidden={!open}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </span>

        <span
          className={`absolute transition-all duration-200 ${
            open ? 'opacity-0 -rotate-45 scale-75' : 'opacity-100 rotate-0 scale-100'
          }`}
          aria-hidden={open}
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </span>

        {/* Notification pulse — ping ring + solid dot when closed */}
        {!open && (
          <span className="absolute -top-1 -right-1" aria-label="AI available">
            <span className="animate-ping absolute inline-flex h-3.5 w-3.5 rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex h-3.5 w-3.5 rounded-full bg-emerald-500 border-2 border-white dark:border-zinc-900" />
          </span>
        )}
      </button>
    </div>
  )
}
