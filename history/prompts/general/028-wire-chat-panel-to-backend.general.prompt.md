---
id: "028"
title: "Wire ChatPanel UI to Backend Chat API"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Wire ChatPanel UI to backend /api/chat"
labels: ["phase-iii", "chat-ui", "frontend", "api-integration", "jwt"]
links:
  spec: "specs/api/chat-endpoint.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/lib/api.ts"
  - "frontend/components/ChatWidget.tsx"
  - "frontend/components/ChatPanel.tsx"
  - "frontend/components/TasksView.tsx"
tests: []
---

## Prompt

Wire ChatPanel UI to backend /api/chat.

Requirements:
- On send, call POST {NEXT_PUBLIC_API_URL}/api/chat
- Attach JWT token like other API calls (same method already used for tasks)
- Show messages in ChatPanel:
  - user bubble
  - assistant bubble
- Loading state while waiting
- If 401, show "Session expired, please sign in again"
- Keep existing todo logic unchanged

## Response

Wired ChatPanel to the live POST /api/chat endpoint using the existing
`request()` helper pattern. Zero TypeScript errors across all changed files.
Todo logic untouched.

### frontend/lib/api.ts
Added `ChatResponse` interface (`reply: string`, `trace_id: string`) and
`chatApi.sendMessage(token, message)` using the existing `request<T>()` helper.
Identical pattern to `tasksApi` — Bearer token attached automatically.

### frontend/components/ChatWidget.tsx
Added `token: string` to `ChatWidgetProps` interface. Forwards `token` as a
prop to `<ChatPanel token={token} onClose={...} />`.

### frontend/components/ChatPanel.tsx
Key changes:
- Added `token: string` to `ChatPanelProps`
- Added `import { chatApi, ApiError } from '@/lib/api'`
- Added `loading: boolean` state
- `handleSend` is now `async`:
  - Appends user bubble immediately (optimistic)
  - Clears input, sets `loading = true`
  - Calls `chatApi.sendMessage(token, text)`
  - On success → appends `{ role: 'assistant', content: data.reply }` bubble
  - On `ApiError` with status 401 → appends `"Session expired, please sign in again."`
  - On any other error → appends `"Something went wrong. Please try again."`
  - `finally` → sets `loading = false`
- Added animated typing indicator (three bouncing dots) rendered below messages while `loading === true`
- Input and send button disabled while `loading === true`; placeholder changes to "Waiting for reply…"
- `useEffect` dependency array updated to include `loading` so auto-scroll triggers when indicator appears
- Welcome message updated: removed "(Backend coming in Phase III)" — the endpoint is now live
- Fixed two Tailwind v4 canonical class warnings: `h-[460px]` → `h-115`, `bg-gradient-to-r` → `bg-linear-to-r`

### frontend/components/TasksView.tsx
Changed `<ChatWidget />` to `<ChatWidget token={token} />`. Single-line change;
all other task logic untouched.

## Outcome

- [x] POST /api/chat called on send with Bearer JWT
- [x] User bubble appears immediately on send
- [x] Assistant bubble appears when reply arrives
- [x] Animated typing indicator shown while awaiting reply
- [x] 401 → "Session expired, please sign in again."
- [x] Other errors → "Something went wrong. Please try again."
- [x] Input + send disabled during in-flight request
- [x] Zero TypeScript errors (all files)
- [x] Zero Tailwind warnings (ChatPanel)
- [x] Todo logic (TasksView, tasks routes) untouched
