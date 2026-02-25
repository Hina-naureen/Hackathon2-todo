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

// Tools that mutate task data — used to trigger task list highlight
const MUTATION_TOOLS = new Set(['create_task', 'update_task', 'toggle_complete'])

interface ChatPanelProps {
  token: string
  onClose: () => void
  onMutation?: () => void
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
// AI avatar — gradient circle with star icon
// ---------------------------------------------------------------------------

function AiAvatar() {
  return (
    <div
      className="flex-shrink-0 w-6 h-6 rounded-full bg-linear-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-sm"
      aria-hidden="true"
    >
      <svg width="11" height="11" viewBox="0 0 24 24" fill="white">
        <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
      </svg>
    </div>
  )
}

// ---------------------------------------------------------------------------
// ChatPanel
// ---------------------------------------------------------------------------

export default function ChatPanel({ token, onClose, onMutation }: ChatPanelProps) {
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
      // Trigger task list highlight if any mutation tool was called
      if (data.actions?.some(a => MUTATION_TOOLS.has(a.tool))) {
        onMutation?.()
      }
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
    <div className="flex flex-col w-80 h-115 rounded-2xl backdrop-blur-md bg-white/90 border border-violet-200/50 shadow-[0_8px_32px_rgba(139,92,246,0.12),0_2px_8px_rgba(0,0,0,0.08)] overflow-hidden dark:bg-zinc-900/90 dark:border-violet-800/30 dark:shadow-[0_8px_32px_rgba(139,92,246,0.18),0_2px_8px_rgba(0,0,0,0.3)]">

      {/* Gradient header bar — Phase III Preview */}
      <div className="relative flex items-center justify-between px-4 py-3 bg-linear-to-r from-violet-600 via-purple-600 to-blue-600 overflow-hidden">
        {/* Subtle shine */}
        <div className="absolute inset-0 bg-white/10" aria-hidden="true" />

        {/* Left: pulsing dot + title + subtitle */}
        <div className="relative flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400" />
          </span>
          <div>
            <p className="text-xs font-bold text-white leading-none">AI Assistant</p>
            <p className="text-[10px] font-medium text-white/70 leading-none mt-0.5 uppercase tracking-widest">
              Phase III Preview
            </p>
          </div>
        </div>

        {/* Right: close button */}
        <button
          onClick={onClose}
          className="relative p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/20 transition-colors"
          aria-label="Close chat"
        >
          <svg
            width="15"
            height="15"
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
            className={`msg-in flex items-end gap-2 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {/* AI avatar — only for assistant messages */}
            {msg.role === 'assistant' && <AiAvatar />}

            <div
              className={`max-w-[75%] px-3 py-2 rounded-2xl text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-slate-900 text-white rounded-br-sm dark:bg-white dark:text-slate-900'
                  : 'bg-slate-100 text-slate-700 rounded-bl-sm dark:bg-zinc-800 dark:text-zinc-200'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Typing indicator — bouncing dots + "AI is typing…" label */}
        {loading && (
          <div className="msg-in flex items-end gap-2 justify-start">
            <AiAvatar />
            <div className="flex items-center gap-2 px-3 py-2.5 rounded-2xl rounded-bl-sm bg-slate-100 dark:bg-zinc-800">
              <span className="flex gap-1 items-center">
                <span
                  className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce"
                  style={{ animationDelay: '0ms' }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce"
                  style={{ animationDelay: '150ms' }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-zinc-500 animate-bounce"
                  style={{ animationDelay: '300ms' }}
                />
              </span>
              <span className="text-[11px] text-slate-400 dark:text-zinc-500 italic">
                AI is typing…
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
            className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-violet-500 transition-all duration-200 bg-white disabled:opacity-50 disabled:cursor-not-allowed dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-violet-400"
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-9 h-9 flex items-center justify-center rounded-xl bg-linear-to-br from-violet-600 to-purple-600 text-white hover:opacity-90 disabled:opacity-40 transition-all duration-200 hover:scale-105 shadow-sm"
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
