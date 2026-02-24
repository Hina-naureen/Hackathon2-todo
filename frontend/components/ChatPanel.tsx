'use client'

import { useState, useRef, useEffect } from 'react'
import { chatApi, ApiError } from '@/lib/api'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

interface ChatPanelProps {
  token: string
  onClose: () => void
}

// ---------------------------------------------------------------------------
// Seed message shown on open
// ---------------------------------------------------------------------------

const WELCOME: Message = {
  id: 0,
  role: 'assistant',
  content: "Hi! I'm your AI assistant. Ask me anything about your tasks.",
}

// ---------------------------------------------------------------------------
// ChatPanel
// ---------------------------------------------------------------------------

export default function ChatPanel({ token, onClose }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([WELCOME])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    // Append user bubble immediately
    const userMsg: Message = { id: Date.now(), role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await chatApi.sendMessage(token, text)
      setMessages(prev => [
        ...prev,
        { id: Date.now(), role: 'assistant', content: data.reply },
      ])
    } catch (err) {
      const content =
        err instanceof ApiError && err.status === 401
          ? 'Session expired, please sign in again.'
          : 'Something went wrong. Please try again.'
      setMessages(prev => [
        ...prev,
        { id: Date.now(), role: 'assistant', content },
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col w-80 h-115 rounded-2xl backdrop-blur-md bg-white/90 shadow-xl border border-white/60 overflow-hidden dark:bg-zinc-900/90 dark:border-zinc-700/60">

      {/* Phase III preview banner */}
      <div className="flex items-center justify-center gap-1.5 px-4 py-1.5 bg-linear-to-r from-violet-500/10 via-purple-500/10 to-blue-500/10 border-b border-purple-200/40 dark:border-purple-800/30">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-purple-600 dark:text-purple-400">
          Phase III Preview
        </span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100/80 dark:border-zinc-700/60 bg-white/60 dark:bg-zinc-800/60 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
            AI Assistant
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors dark:text-zinc-500 dark:hover:text-zinc-200 dark:hover:bg-zinc-700"
          aria-label="Close chat"
        >
          <svg
            width="16"
            height="16"
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
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[78%] px-3 py-2 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-slate-900 text-white rounded-br-sm dark:bg-white dark:text-slate-900'
                  : 'bg-slate-100 text-slate-700 rounded-bl-sm dark:bg-zinc-800 dark:text-zinc-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Typing indicator — shown while awaiting backend response */}
        {loading && (
          <div className="flex justify-start">
            <div className="px-3 py-3 rounded-2xl rounded-bl-sm bg-slate-100 dark:bg-zinc-800">
              <span className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce" style={{ animationDelay: '300ms' }} />
              </span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-gray-100/80 dark:border-zinc-700/60 bg-white/60 dark:bg-zinc-800/60 backdrop-blur-sm">
        <div className="flex gap-2 items-center">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={loading ? 'Waiting for reply…' : 'Ask anything…'}
            disabled={loading}
            className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 bg-white disabled:opacity-50 disabled:cursor-not-allowed dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-slate-900 text-white hover:bg-slate-700 disabled:opacity-40 transition-all duration-200 hover:scale-105 dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
            aria-label="Send message"
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
