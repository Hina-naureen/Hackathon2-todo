import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Evolution of Todo',
  description: 'Phase II — full-stack todo app',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
