// lib/api.ts — typed FastAPI client for Phase II
// All calls attach Bearer token from the session.

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export interface Task {
  id: number
  title: string
  description: string
  completed: boolean
  created_at: string  // ISO 8601 UTC
  updated_at: string  // ISO 8601 UTC
}

export interface CreateTaskInput {
  title: string
  description?: string
}

export interface UpdateTaskInput {
  title?: string | null       // null = keep existing
  description?: string | null // null = keep existing
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new ApiError(res.status, (body as { detail?: string }).detail ?? 'Unknown error')
  }

  return res.json() as Promise<T>
}

export interface ChatActionItem {
  tool: string
  args: Record<string, unknown>
  result: unknown
}

export interface ChatResponse {
  reply: string
  trace_id: string
  actions: ChatActionItem[]
}

export const chatApi = {
  sendMessage: (token: string, message: string) =>
    request<ChatResponse>('/api/chat', token, {
      method: 'POST',
      body: JSON.stringify({ message }),
    }),
}

export const tasksApi = {
  getTasks: (token: string) =>
    request<Task[]>('/api/tasks', token),

  createTask: (token: string, data: CreateTaskInput) =>
    request<Task>('/api/tasks', token, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateTask: (token: string, id: number, data: UpdateTaskInput) =>
    request<Task>(`/api/tasks/${id}`, token, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteTask: (token: string, id: number) =>
    request<{ detail: string }>(`/api/tasks/${id}`, token, { method: 'DELETE' }),

  toggleTask: (token: string, id: number) =>
    request<Task>(`/api/tasks/${id}/toggle`, token, { method: 'PATCH' }),
}
