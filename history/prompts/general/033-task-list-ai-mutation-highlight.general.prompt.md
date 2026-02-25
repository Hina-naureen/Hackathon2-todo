---
id: "033"
title: "Task List AI Mutation Highlight"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Trigger subtle UI highlight on task list area when AI replies with add/delete/update intent"
labels: ["phase-iii", "chat-ui", "frontend", "visual-feedback", "tailwind"]
links:
  spec: "specs/api/chat-endpoint.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/app/globals.css"
  - "frontend/lib/api.ts"
  - "frontend/components/ChatPanel.tsx"
  - "frontend/components/ChatWidget.tsx"
  - "frontend/components/TasksView.tsx"
tests: []
---

## Prompt

When AI replies with add/delete/update intent, trigger subtle UI highlight on task list area.

No backend changes. Only frontend visual feedback.

## Response

### frontend/app/globals.css

Added `@keyframes task-highlight` + `.task-list-highlight` utility:
- Violet ring (`rgba(139,92,246,...)`) pulses in over 20% of 1.3s then fades to zero
- `border-radius: 12px` matches the task card shape

### frontend/lib/api.ts

Added `ChatActionItem` interface and `actions: ChatActionItem[]` field to `ChatResponse`:
- Backend already returns `actions`; frontend was discarding it
- `tool: string` is used to detect mutation intent

### frontend/components/ChatPanel.tsx

- Added `MUTATION_TOOLS = new Set(['create_task', 'update_task', 'toggle_complete'])`
- Added `onMutation?: () => void` to `ChatPanelProps`
- After successful response: `if (data.actions?.some(a => MUTATION_TOOLS.has(a.tool))) onMutation?.()`

### frontend/components/ChatWidget.tsx

- Added `onMutation?: () => void` to `ChatWidgetProps`
- Forwarded to `<ChatPanel onMutation={onMutation} />`

### frontend/components/TasksView.tsx

- Added `useRef` import
- Added `taskListHighlighted: boolean` state + `highlightTimer` ref
- Added `triggerHighlight` callback: clears previous timer, removes class for one `requestAnimationFrame` to restart the CSS animation on repeated calls, re-applies class, sets 1400ms timeout to clear
- Wrapped task list conditional (`empty state` / `task cards`) in `<div className={taskListHighlighted ? 'task-list-highlight' : ''}>`
- `<ChatWidget onMutation={triggerHighlight} />`

## Outcome

- [x] Violet glow ring appears on task list whenever AI calls create_task, update_task, or toggle_complete
- [x] Animation auto-clears after 1.3s; re-triggerable without visual stutter
- [x] Works for both empty-state and populated task list
- [x] No backend files changed
- [x] Zero TypeScript errors (`tsc --noEmit` clean)
- [x] Dark mode compatible (CSS box-shadow, not Tailwind ring)
