// app/page.tsx — root redirect (middleware handles the actual redirect,
// this component is a fallback for SSR)
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'

export default async function RootPage() {
  const session = await getSession()
  redirect(session ? '/tasks' : '/sign-in')
}
