---
id: "038"
title: "Phase V AI Action Trigger"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade to Phase V – AI UI Action Trigger: Create Task button opens Add Task modal"
labels: ["phase-v", "chat-ui", "frontend", "custom-event", "modal-trigger"]
links:
  spec: "specs/features/chatbot.md"
  ticket: "null"
  adr: "null"
  pr: "null"
files:
  - "frontend/components/ChatPanel.tsx"
  - "frontend/components/TasksView.tsx"
tests: []
---

## Prompt

When user clicks "+ Create Task" inside ChatPanel, open the existing Add Task modal.
Dispatch custom event from ChatPanel; listen in TasksView. No backend changes.

## Response

### frontend/components/ChatPanel.tsx (1 line changed)

Button `onClick` — replaced `console.log` with event dispatch:
```ts
onClick={() => window.dispatchEvent(new Event('open-add-task'))}
```

### frontend/components/TasksView.tsx (2 changes)

1. Added `useEffect` to the React import.

2. Added listener after `triggerHighlight`:
```ts
useEffect(() => {
  const open = () => setModal({ type: 'add' })
  window.addEventListener('open-add-task', open)
  return () => window.removeEventListener('open-add-task', open)
}, [])
```
`setModal({ type: 'add' })` is the existing call already used by the "+ Add Task" button —
no new modal code, no new state. The listener is cleaned up on unmount.

## Outcome

- [x] Clicking "+ Create Task" in ChatPanel opens the Add Task modal
- [x] Event-based decoupling — ChatPanel has no import of TasksView
- [x] Listener removed on unmount (no leak)
- [x] Todo logic, backend, and all styling unchanged
- [x] Zero TypeScript errors
