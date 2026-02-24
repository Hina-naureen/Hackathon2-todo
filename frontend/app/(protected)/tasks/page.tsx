// app/(protected)/tasks/page.tsx — server component
// Checks session, fetches initial tasks, passes token + data to client component.

import { redirect } from 'next/navigation'
import { getSession, getToken } from '@/lib/auth'
import { tasksApi, Task } from '@/lib/api'
import TasksView from '@/components/TasksView'

export default async function TasksPage() {
  const session = await getSession()
  if (!session) redirect('/sign-in')

  const token = await getToken()
  if (!token) redirect('/sign-in')

  let initialTasks: Task[] = []
  try {
    initialTasks = await tasksApi.getTasks(token)
  } catch {
    // Backend may be offline; client will show empty list + let user retry
  }

  return (
    <TasksView
      initialTasks={initialTasks}
      token={token}
      userEmail={session.email}
      userName={session.name}
    />
  )
}
