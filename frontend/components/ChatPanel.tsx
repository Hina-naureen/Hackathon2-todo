'use client'

import { useState, useRef, useEffect, Fragment } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  showAction?: boolean   // true when the "add" keyword was detected — renders Create Task button
  taskTitle?: string     // extracted task subject — sent as prefillTitle to the modal
  priority?: 'high' | 'medium' | 'normal'  // detected from urgency/time keywords
}

interface ChatPanelProps {
  token: string
  onClose: () => void
  onMutation?: () => void
  pendingTaskCount: number
  onAITaskCreate: (title: string, priority: 'high' | 'medium' | 'normal') => void
}

// ---------------------------------------------------------------------------
// Phase IV — Smart AI simulation layer
// No external API. Keyword detection + contextual replies.
// ---------------------------------------------------------------------------

/**
 * Strips intent keywords from the raw message to isolate the task subject.
 *   "add homework tomorrow" → "homework"
 *   "urgent meeting today"  → ""  (no subject left)
 */
function extractTask(raw: string): string {
  return raw
    .replace(
      /\b(add|create|make|schedule|put|set|today|tomorrow|urgent|please|a|an|the)\b/gi,
      ''
    )
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * simulateAI — fake AI brain with keyword detection.
 *
 * Detects intent from the user message and returns a contextual reply.
 * Rules checked in priority order (most specific → most general).
 * Always returns a non-empty string — never falls through to a backend.
 *
 * Recognised keywords: add, today, tomorrow, urgent, homework, meeting
 */
function simulateAI(message: string): string {
  const t = message.toLowerCase()
  const task = extractTask(message)
  const label = task || 'this task'

  // --- compound patterns (most specific first) ---

  if (t.includes('add') && t.includes('urgent')) {
    return `That sounds urgent! Should I create a high-priority task called "${label}"?`
  }

  if (t.includes('urgent') && t.includes('meeting')) {
    return `This sounds important. I recommend marking it as high priority.`
  }

  if (t.includes('add') && t.includes('homework')) {
    return `I suggest creating a homework task. Should I add it to your list?`
  }

  if (t.includes('add') && t.includes('meeting')) {
    return `I can add a meeting task for you. Want me to create it?`
  }

  if (t.includes('add') && t.includes('today')) {
    return `Got it! I can add that for today. Want me to create "${label}"?`
  }

  if (t.includes('add') && t.includes('tomorrow')) {
    return `I suggest creating a task for tomorrow. Should I add "${label}"?`
  }

  // --- single keywords ---

  if (t.includes('add')) {
    return `Sure! Should I create a task called "${label}"?`
  }

  if (t.includes('urgent')) {
    return `That sounds important! Would you like me to add this as an urgent task?`
  }

  if (t.includes('homework')) {
    return `Sounds like a study task! Want me to add it to your list?`
  }

  if (t.includes('meeting')) {
    return `Got it, a meeting! Should I schedule it as a task?`
  }

  if (t.includes('today')) {
    return `Would you like me to schedule something for today? Just tell me what to add!`
  }

  if (t.includes('tomorrow')) {
    return `Should I create a task for tomorrow? Tell me what you need!`
  }

  // --- fallback ---
  return `Tell me more about your task so I can help.`
}

/**
 * detectPriority — maps time/urgency keywords to a priority level.
 *   "urgent" | "today"    → high
 *   "tomorrow" | "homework" → medium
 *   everything else         → normal
 */
function detectPriority(text: string): 'high' | 'medium' | 'normal' {
  const t = text.toLowerCase()
  if (t.includes('today') || t.includes('urgent')) return 'high'
  if (t.includes('tomorrow') || t.includes('homework')) return 'medium'
  return 'normal'
}

// Delay (ms) used only when falling back to local simulation
const AI_THINKING_DELAY = 700

// Tools that mutate the task list — trigger a refresh when any of these run
const MUTATION_TOOLS = new Set(['create_task', 'update_task', 'delete_task', 'toggle_complete'])

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

export default function ChatPanel({ token, onClose, onMutation, pendingTaskCount, onAITaskCreate }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Phase IX — smart greeting on mount based on current task state
  useEffect(() => {
    const content =
      pendingTaskCount > 0
        ? `You have ${pendingTaskCount} pending task${pendingTaskCount === 1 ? '' : 's'}. Want help organizing them?`
        : "You're all caught up! Want to plan something new?"
    setMessages([{ id: Date.now(), role: 'assistant', content }])
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    // Append user bubble immediately
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      // --- Real backend call via POST /api/chat ---
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          // Provide today's date so the agent can resolve relative phrases
          // like "tomorrow" or "next Friday" without ambiguity.
          today: new Date().toISOString().split('T')[0],
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const data = await res.json() as { reply: string; actions: { tool: string }[] }

      // Refresh task list when the agent mutated any tasks
      if (data.actions.some(a => MUTATION_TOOLS.has(a.tool))) {
        onMutation?.()
      }

      setMessages(prev => [
        ...prev,
        { id: Date.now(), role: 'assistant', content: data.reply },
      ])
    } catch {
      // --- Fallback: local keyword simulation (no network / no key) ---
      await new Promise(resolve => setTimeout(resolve, AI_THINKING_DELAY))
      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: simulateAI(text),
          showAction: text.toLowerCase().includes('add'),
          taskTitle: extractTask(text),
          priority: detectPriority(text),
        },
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
              Phase III · Live
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
          <Fragment key={msg.id}>
            {/* Message bubble */}
            <div
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

            {/* Action button — shown below AI reply when "add" keyword was detected */}
            {msg.role === 'assistant' && msg.showAction && (
              <div className="msg-in flex justify-start pl-8">
                <button
                  onClick={() => onAITaskCreate(msg.taskTitle ?? '', msg.priority ?? 'normal')}
                  className="px-3 py-1.5 text-xs font-medium rounded-xl bg-slate-900 text-white hover:scale-105 active:scale-95 transition-all duration-200 dark:bg-white dark:text-slate-900"
                >
                  + Create Task
                </button>
              </div>
            )}
          </Fragment>
        ))}

        {/* Typing indicator — driven by existing loading state, no new state added */}
        {loading && (
          <div className="flex gap-1 px-3 py-2">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100" />
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200" />
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
