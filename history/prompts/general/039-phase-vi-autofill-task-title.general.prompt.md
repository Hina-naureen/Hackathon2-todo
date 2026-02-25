---
id: "039"
title: "Phase VI Autofill Task Title from AI"
stage: general
date: "2026-02-25"
surface: agent
model: claude-sonnet-4-6
feature: "none"
branch: master
user: Hina-naureen
command: "Upgrade to Phase VI – Auto Fill Task Title from AI via CustomEvent"
labels: ["phase-vi", "chat-ui", "frontend", "custom-event", "modal-prefill"]
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

When "+ Create Task" is clicked from ChatPanel, send the extracted task text to
the Add Task modal and auto-fill the Title input via CustomEvent detail.

## Response

### frontend/components/ChatPanel.tsx (3 edits)

1. `Message` interface — added `taskTitle?: string`:
   Stores the result of `extractTask(text)` when a message is appended.

2. `handleSend` — stores extracted title in the message object:
   ```ts
   taskTitle: extractTask(text)
   ```

3. Button `onClick` — upgraded from `Event` to `CustomEvent` with detail:
   ```ts
   window.dispatchEvent(
     new CustomEvent('open-add-task', { detail: { title: msg.taskTitle ?? '' } })
   )
   ```

### frontend/components/TasksView.tsx (3 edits)

1. `ModalState` union — extended add variant:
   ```ts
   | { type: 'add'; prefillTitle?: string }
   ```

2. Event listener — cast to `CustomEvent<{ title?: string }>` and extracts title:
   ```ts
   const open = (e: Event) => {
     const title = (e as CustomEvent<{ title?: string }>).detail?.title ?? ''
     setModal({ type: 'add', prefillTitle: title })
   }
   ```

3. `TaskFormModal` (add case) — passes `initialTitle`:
   ```tsx
   initialTitle={modal.prefillTitle}
   ```
   `TaskFormModal` already accepted `initialTitle?: string` and seeds its
   local `title` state from it — no changes to the modal component needed.

## Outcome

- [x] "add homework tomorrow" → button click → modal opens with "homework" pre-filled
- [x] "add meeting" → modal opens with "meeting" pre-filled
- [x] "add" alone (no subject) → modal opens with empty title (unchanged behaviour)
- [x] Direct "+ Add Task" button still works exactly as before
- [x] No changes to TaskFormModal, backend, or styling
- [x] Zero TypeScript errors
