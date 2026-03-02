'use client'

import { useState, useRef, useEffect, Fragment } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface PendingTask {
  title: string
  due_date?: string
  description?: string
}

interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  pendingTask?: PendingTask   // task preview — shows "Create Task" button
  taskCreated?: boolean       // true after the user confirms task creation
  showAction?: boolean        // legacy fallback flag
  taskTitle?: string
  priority?: 'high' | 'medium' | 'normal'
}

interface ChatPanelProps {
  token: string
  onClose: () => void
  onMutation?: () => void
  pendingTaskCount: number
  onAITaskCreate: (title: string, priority: 'high' | 'medium' | 'normal') => void
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Returns true when the message looks like a task-creation request.
 * Used to decide whether to send confirm:false to the backend.
 */
function isCreateIntent(msg: string): boolean {
  return /\b(add|create|make|new|schedule|remind)\b/i.test(msg)
}

/**
 * Strips intent keywords from the raw message to isolate the task subject.
 *   "add homework tomorrow" → "homework"
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

function simulateAI(message: string): string {
  const t = message.toLowerCase()
  const task = extractTask(message)
  const label = task || 'this task'

  if (t.includes('add') && t.includes('urgent')) return `That sounds urgent! I'll prepare a high-priority task called "${label}".`
  if (t.includes('add') && t.includes('meeting')) return `I can add a meeting task for you.`
  if (t.includes('add') && t.includes('today')) return `Got it! I'll add "${label}" for today.`
  if (t.includes('add') && t.includes('tomorrow')) return `I'll prepare a task for tomorrow called "${label}".`
  if (t.includes('add')) return `Ready to create a task called "${label}".`
  if (t.includes('urgent')) return `That sounds important! Would you like me to add this as an urgent task?`
  if (t.includes('meeting')) return `Got it, a meeting! Should I schedule it as a task?`
  if (t.includes('today')) return `Would you like me to schedule something for today?`
  if (t.includes('tomorrow')) return `Should I create a task for tomorrow?`
  return `Tell me more about your task so I can help.`
}

function detectPriority(text: string): 'high' | 'medium' | 'normal' {
  const t = text.toLowerCase()
  if (t.includes('today') || t.includes('urgent')) return 'high'
  if (t.includes('tomorrow') || t.includes('homework')) return 'medium'
  return 'normal'
}

/** Format ISO date string for display: "2026-03-06T09:00:00" → "Fri, 6 Mar" */
function formatDueDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      weekday: 'short', day: 'numeric', month: 'short',
    })
  } catch {
    return iso.slice(0, 10)
  }
}

const AI_THINKING_DELAY = 700
const MUTATION_TOOLS = new Set(['create_task', 'update_task', 'delete_task', 'toggle_complete'])

// ---------------------------------------------------------------------------
// AI avatar
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
  const [creatingId, setCreatingId] = useState<number | null>(null) // which msg has in-flight create
  const bottomRef = useRef<HTMLDivElement>(null)

  // Smart greeting on mount
  useEffect(() => {
    const content =
      pendingTaskCount > 0
        ? `You have ${pendingTaskCount} pending task${pendingTaskCount === 1 ? '' : 's'}. Want help organizing them?`
        : "You're all caught up! Want to plan something new?"
    setMessages([{ id: Date.now(), role: 'assistant', content }])
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // ── Create Task button handler ──────────────────────────────────────────
  async function handleCreateTask(msgId: number, task: PendingTask) {
    setCreatingId(msgId)
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
      const res = await fetch(`${apiUrl}/api/tasks`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          title: task.title,
          description: task.description ?? '',
          ...(task.due_date ? { due_date: task.due_date } : {}),
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      // Mark message as confirmed (hide the button, update reply text)
      setMessages(prev =>
        prev.map(m =>
          m.id === msgId
            ? {
                ...m,
                content: `Task "${task.title}" added to your list!`,
                pendingTask: undefined,
                taskCreated: true,
              }
            : m
        )
      )
      onMutation?.()
    } catch {
      setMessages(prev =>
        prev.map(m =>
          m.id === msgId ? { ...m, content: `Failed to create task. Please try again.` } : m
        )
      )
    } finally {
      setCreatingId(null)
    }
  }

  // ── Send handler ────────────────────────────────────────────────────────
  async function handleSend() {
    const text = input.trim()
    if (!text || loading) return

    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: text }])
    setInput('')
    setLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
      const createIntent = isCreateIntent(text)

      const res = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text,
          today: new Date().toISOString().split('T')[0],
          // Preview mode for create intents — backend extracts without persisting
          confirm: !createIntent,
        }),
      })

      if (!res.ok) throw new Error(`HTTP ${res.status}`)

      const data = await res.json() as {
        reply: string
        actions: { tool: string }[]
        pending_task?: PendingTask
      }

      // Non-create actions (list, delete, toggle) → refresh task list
      if (data.actions.some(a => MUTATION_TOOLS.has(a.tool))) {
        onMutation?.()
      }

      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: data.reply,
          pendingTask: data.pending_task ?? undefined,
        },
      ])
    } catch {
      // ── Fallback: local simulation ──────────────────────────────────────
      await new Promise(resolve => setTimeout(resolve, AI_THINKING_DELAY))
      const createIntent = isCreateIntent(text)
      const taskTitle = extractTask(text)

      setMessages(prev => [
        ...prev,
        {
          id: Date.now(),
          role: 'assistant',
          content: simulateAI(text),
          // For create intents, show a pending task card even in fallback mode
          pendingTask: createIntent && taskTitle ? { title: taskTitle[0].toUpperCase() + taskTitle.slice(1) } : undefined,
          // Legacy fallback for onAITaskCreate modal (kept for non-create intents)
          showAction: !createIntent && text.toLowerCase().includes('add'),
          taskTitle,
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

      {/* Header */}
      <div className="relative flex items-center justify-between px-4 py-3 bg-linear-to-r from-violet-600 via-purple-600 to-blue-600 overflow-hidden">
        <div className="absolute inset-0 bg-white/10" aria-hidden="true" />
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
        <button
          onClick={onClose}
          className="relative p-1.5 rounded-lg text-white/70 hover:text-white hover:bg-white/20 transition-colors"
          aria-label="Close chat"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
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
            <div className={`msg-in flex items-end gap-2 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
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

            {/* ── Pending task preview card ──────────────────────────────── */}
            {msg.role === 'assistant' && msg.pendingTask && !msg.taskCreated && (
              <div className="msg-in flex justify-start pl-8">
                <div className="rounded-xl border border-violet-200 bg-violet-50 dark:bg-violet-950/40 dark:border-violet-700/50 px-3 py-2.5 flex flex-col gap-2 w-48">
                  {/* Task info */}
                  <div className="flex flex-col gap-0.5">
                    <p className="text-xs font-semibold text-slate-800 dark:text-zinc-100 leading-tight">
                      {msg.pendingTask.title}
                    </p>
                    {msg.pendingTask.due_date && (
                      <p className="text-[11px] text-violet-600 dark:text-violet-400 flex items-center gap-1">
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
                          <line x1="16" y1="2" x2="16" y2="6" />
                          <line x1="8" y1="2" x2="8" y2="6" />
                          <line x1="3" y1="10" x2="21" y2="10" />
                        </svg>
                        {formatDueDate(msg.pendingTask.due_date)}
                      </p>
                    )}
                    <span className="text-[10px] font-medium text-amber-600 dark:text-amber-400 uppercase tracking-wide">
                      Pending
                    </span>
                  </div>

                  {/* Create Task button */}
                  <button
                    onClick={() => handleCreateTask(msg.id, msg.pendingTask!)}
                    disabled={creatingId === msg.id}
                    className="w-full py-1.5 text-xs font-semibold rounded-lg bg-violet-600 text-white hover:bg-violet-700 active:scale-95 transition-all duration-150 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-1"
                  >
                    {creatingId === msg.id ? (
                      <>
                        <svg className="animate-spin w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" strokeLinecap="round" />
                        </svg>
                        Adding…
                      </>
                    ) : (
                      <>
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                        Create Task
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Legacy showAction button (non-create fallback) */}
            {msg.role === 'assistant' && msg.showAction && !msg.pendingTask && (
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

        {/* Typing indicator */}
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <line x1="12" y1="19" x2="12" y2="5" />
              <polyline points="5 12 12 5 19 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
