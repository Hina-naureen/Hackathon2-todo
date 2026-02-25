'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import Header from './Header'
import ChatWidget from './ChatWidget'
import { Task, tasksApi, ApiError, CreateTaskInput, UpdateTaskInput } from '@/lib/api'

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  initialTasks: Task[]
  token: string
  userEmail: string
  userName: string
}

// ---------------------------------------------------------------------------
// Modal state discriminated union
// ---------------------------------------------------------------------------

type ModalState =
  | null
  | { type: 'add'; prefillTitle?: string }
  | { type: 'edit'; task: Task }
  | { type: 'delete'; task: Task }

// ---------------------------------------------------------------------------
// Main TasksView component
// ---------------------------------------------------------------------------

export default function TasksView({ initialTasks, token, userEmail, userName }: Props) {
  const [tasks, setTasks] = useState<Task[]>(initialTasks)
  const [modal, setModal] = useState<ModalState>(null)
  const [toast, setToast] = useState<string | null>(null)
  const [togglingIds, setTogglingIds] = useState<Set<number>>(new Set())
  const [taskListHighlighted, setTaskListHighlighted] = useState(false)
  const highlightTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const triggerHighlight = useCallback(() => {
    if (highlightTimer.current) clearTimeout(highlightTimer.current)
    setTaskListHighlighted(false)
    // One frame gap ensures CSS animation restarts if called in quick succession
    requestAnimationFrame(() => {
      setTaskListHighlighted(true)
      highlightTimer.current = setTimeout(() => setTaskListHighlighted(false), 1400)
    })
  }, [])

  // Phase VI — open Add Task modal and prefill title from ChatPanel's CustomEvent
  useEffect(() => {
    const open = (e: Event) => {
      const title = (e as CustomEvent<{ title?: string }>).detail?.title ?? ''
      setModal({ type: 'add', prefillTitle: title })
    }
    window.addEventListener('open-add-task', open)
    return () => window.removeEventListener('open-add-task', open)
  }, [])

  const showToast = useCallback((msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 4000)
  }, [])

  const handleApiError = useCallback(
    (err: unknown) => {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          window.location.href = '/sign-in'
          return
        }
        if (err.status === 404) {
          showToast('Task not found.')
          tasksApi.getTasks(token).then(setTasks).catch(() => {})
          return
        }
        showToast(err.message || 'Something went wrong. Please try again.')
      } else {
        showToast('Could not connect to the server.')
      }
    },
    [token, showToast]
  )

  // Toggle with optimistic UI + revert on error
  async function handleToggle(task: Task) {
    setTogglingIds(prev => new Set([...prev, task.id]))
    setTasks(prev =>
      prev.map(t => (t.id === task.id ? { ...t, completed: !t.completed } : t))
    )
    try {
      const updated = await tasksApi.toggleTask(token, task.id)
      setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)))
    } catch (err) {
      // Revert optimistic update
      setTasks(prev => prev.map(t => (t.id === task.id ? task : t)))
      handleApiError(err)
    } finally {
      setTogglingIds(prev => {
        const s = new Set(prev)
        s.delete(task.id)
        return s
      })
    }
  }

  async function handleAdd(title: string, description: string): Promise<void> {
    const task = await tasksApi.createTask(token, { title, description } as CreateTaskInput)
    setTasks(prev => [...prev, task])
    setModal(null)
  }

  async function handleEdit(task: Task, title: string, description: string): Promise<void> {
    const data: UpdateTaskInput = {
      title: title !== task.title ? title : null,
      description: description !== task.description ? description : null,
    }
    const updated = await tasksApi.updateTask(token, task.id, data)
    setTasks(prev => prev.map(t => (t.id === updated.id ? updated : t)))
    setModal(null)
  }

  async function handleDelete(task: Task) {
    try {
      await tasksApi.deleteTask(token, task.id)
      setTasks(prev => prev.filter(t => t.id !== task.id))
      setModal(null)
    } catch (err) {
      handleApiError(err)
      setModal(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-zinc-900">
      <Header userEmail={userEmail} userName={userName} />

      {/* Toast notification */}
      {toast && (
        <div className="fixed top-4 right-4 bg-slate-900 text-white px-4 py-2.5 rounded-xl shadow-lg z-50 text-sm">
          {toast}
        </div>
      )}

      {/* Main content */}
      <main className="max-w-3xl mx-auto px-6 py-10">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-slate-900 dark:text-white">
              My Tasks
            </h1>
            <p className="text-sm text-slate-500 mt-0.5 dark:text-zinc-400">
              {tasks.length} {tasks.length === 1 ? 'task' : 'tasks'}
            </p>
          </div>
          <button
            onClick={() => setModal({ type: 'add' })}
            className="bg-slate-900 text-white px-4 py-2 rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
          >
            + Add Task
          </button>
        </div>

        {/* Task list — highlight wrapper reacts to AI mutations */}
        <div className={taskListHighlighted ? 'task-list-highlight' : ''}>
          {tasks.length === 0 ? (
            <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-16 text-center dark:bg-zinc-800 dark:border-zinc-800">
              <p className="text-slate-400 text-sm dark:text-zinc-500">
                No tasks yet. Add your first task.
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {tasks.map(task => (
                <TaskItem
                  key={task.id}
                  task={task}
                  toggling={togglingIds.has(task.id)}
                  onToggle={() => handleToggle(task)}
                  onEdit={() => setModal({ type: 'edit', task })}
                  onDelete={() => setModal({ type: 'delete', task })}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      {modal?.type === 'add' && (
        <TaskFormModal
          heading="Add Task"
          submitLabel="Add Task"
          initialTitle={modal.prefillTitle}
          onClose={() => setModal(null)}
          onSubmit={handleAdd}
        />
      )}
      {modal?.type === 'edit' && (
        <TaskFormModal
          heading="Edit Task"
          submitLabel="Save changes"
          initialTitle={modal.task.title}
          initialDescription={modal.task.description}
          onClose={() => setModal(null)}
          onSubmit={(title, desc) => handleEdit(modal.task, title, desc)}
        />
      )}
      {modal?.type === 'delete' && (
        <DeleteModal
          task={modal.task}
          onClose={() => setModal(null)}
          onConfirm={() => handleDelete(modal.task)}
        />
      )}

      {/* Phase III — AI chat widget */}
      <ChatWidget token={token} onMutation={triggerHighlight} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// TaskItem
// ---------------------------------------------------------------------------

interface TaskItemProps {
  task: Task
  toggling: boolean
  onToggle: () => void
  onEdit: () => void
  onDelete: () => void
}

function TaskItem({ task, toggling, onToggle, onEdit, onDelete }: TaskItemProps) {
  const truncated =
    task.description.length > 60
      ? task.description.slice(0, 60) + '…'
      : task.description

  return (
    <div className="flex items-center gap-4 px-5 py-4 bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:scale-[1.01] transition-all duration-200 ease-out dark:bg-zinc-800 dark:border-zinc-800">
      <input
        type="checkbox"
        checked={task.completed}
        onChange={onToggle}
        disabled={toggling}
        className="w-4 h-4 cursor-pointer disabled:cursor-not-allowed accent-slate-900 dark:accent-white"
      />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span
            className={`font-medium text-sm ${
              task.completed
                ? 'line-through text-slate-400 dark:text-zinc-500'
                : 'text-slate-900 dark:text-white'
            }`}
          >
            {task.title}
          </span>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              task.completed
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
                : 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
            }`}
          >
            {task.completed ? 'Completed' : 'Pending'}
          </span>
        </div>
        {task.description && (
          <p className="text-xs text-slate-400 mt-0.5 truncate dark:text-zinc-500">{truncated}</p>
        )}
      </div>
      <button
        onClick={onEdit}
        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-50 transition-colors dark:text-zinc-500 dark:hover:text-zinc-200 dark:hover:bg-zinc-700"
        title="Edit"
        aria-label={`Edit ${task.title}`}
      >
        ✎
      </button>
      <button
        onClick={onDelete}
        className="p-1.5 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors dark:text-zinc-500 dark:hover:text-red-400 dark:hover:bg-red-900/20"
        title="Delete"
        aria-label={`Delete ${task.title}`}
      >
        ×
      </button>
    </div>
  )
}

// ---------------------------------------------------------------------------
// TaskFormModal (shared by Add and Edit)
// ---------------------------------------------------------------------------

interface TaskFormModalProps {
  heading: string
  submitLabel: string
  initialTitle?: string
  initialDescription?: string
  onClose: () => void
  onSubmit: (title: string, description: string) => Promise<void>
}

function TaskFormModal({
  heading,
  submitLabel,
  initialTitle = '',
  initialDescription = '',
  onClose,
  onSubmit,
}: TaskFormModalProps) {
  const [title, setTitle] = useState(initialTitle)
  const [description, setDescription] = useState(initialDescription)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  function validate(): string | null {
    if (!title.trim()) return 'Title is required.'
    if (title.trim().length > 200) return 'Title must be 200 characters or fewer.'
    if (description.length > 500) return 'Description must be 500 characters or fewer.'
    return null
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setLoading(true)
    setError(null)
    try {
      await onSubmit(title.trim(), description)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  function handleBackdropClick(e: React.MouseEvent<HTMLDivElement>) {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div
      className="fixed inset-0 bg-black/30 flex items-center justify-center z-40 px-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 w-full max-w-md p-6 dark:bg-zinc-800 dark:border-zinc-700">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-base font-semibold tracking-tight text-slate-900 dark:text-white">
            {heading}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-colors dark:text-zinc-500 dark:hover:text-zinc-300 dark:hover:bg-zinc-700"
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="task-title" className="block text-xs font-medium text-slate-600 mb-1.5 dark:text-zinc-400">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              id="task-title"
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
              placeholder="Task title"
              autoFocus
            />
          </div>

          <div>
            <label
              htmlFor="task-description"
              className="block text-xs font-medium text-slate-600 mb-1.5 dark:text-zinc-400"
            >
              Description
            </label>
            <input
              id="task-description"
              type="text"
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900 transition-all duration-200 dark:bg-zinc-700 dark:border-zinc-600 dark:text-white dark:placeholder:text-zinc-400 dark:focus:ring-zinc-400"
              placeholder="Optional description"
            />
          </div>

          {error && <p className="text-xs text-red-600">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-slate-600 border border-gray-200 rounded-lg hover:bg-slate-50 transition-colors dark:text-zinc-400 dark:border-zinc-600 dark:hover:bg-zinc-700"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm bg-slate-900 text-white rounded-lg hover:bg-slate-700 disabled:opacity-50 transition-colors dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100"
            >
              {loading ? 'Saving…' : submitLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// DeleteModal
// ---------------------------------------------------------------------------

interface DeleteModalProps {
  task: Task
  onClose: () => void
  onConfirm: () => Promise<void>
}

function DeleteModal({ task, onClose, onConfirm }: DeleteModalProps) {
  const [loading, setLoading] = useState(false)

  async function handleConfirm() {
    setLoading(true)
    await onConfirm()
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-40 px-4">
      <div className="bg-white rounded-2xl shadow-lg border border-gray-100 w-full max-w-sm p-6 dark:bg-zinc-800 dark:border-zinc-700">
        <h2 className="text-base font-semibold tracking-tight text-slate-900 mb-1 dark:text-white">
          Delete task
        </h2>
        <p className="text-sm text-slate-600 mb-1 dark:text-zinc-300">
          &quot;{task.title}&quot; will be permanently removed.
        </p>
        <p className="text-xs text-slate-400 mb-6 dark:text-zinc-500">This cannot be undone.</p>

        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={loading}
            className="px-4 py-2 text-sm text-slate-600 border border-gray-200 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition-colors dark:text-zinc-400 dark:border-zinc-600 dark:hover:bg-zinc-700"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={loading}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}
