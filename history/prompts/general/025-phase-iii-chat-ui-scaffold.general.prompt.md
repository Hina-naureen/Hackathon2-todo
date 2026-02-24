---
id: 025
title: Phase III AI Chat UI Scaffold
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Prepare UI for Phase III AI Chatbot. Requirements: floating chat button bottom-right, chat panel component, Tailwind glassmorphism style, dark mode compatible, no backend logic. Files: components/ChatWidget.tsx, components/ChatPanel.tsx. Design: rounded-2xl, backdrop-blur-md, shadow-xl, hover animations. Do not change existing todo logic."
labels: ["frontend","ui","tailwind","glassmorphism","chat","phase-iii","scaffold"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/components/ChatPanel.tsx (created)
  - frontend/components/ChatWidget.tsx (created)
  - frontend/components/TasksView.tsx (1 import + 1 render line added)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Prepare UI for Phase III AI Chatbot.

Requirements:
- Add floating chat button bottom-right
- Create chat panel component
- Tailwind glassmorphism style
- dark mode compatible
- No backend logic yet

Files:
components/ChatWidget.tsx
components/ChatPanel.tsx

Design:
- rounded-2xl
- backdrop-blur-md
- shadow-xl
- hover animations

Do not change existing todo logic.

## Response snapshot

Two new components created. `TasksView.tsx` touched only to add the import and render `<ChatWidget />` — zero todo logic changed.

**`ChatPanel.tsx`**
- `w-80 h-[460px] rounded-2xl backdrop-blur-md bg-white/90 shadow-xl border border-white/60`
- Header: emerald pulse dot, "AI Assistant · Phase III" label, close button
- Message list: auto-scrolling via `useRef`, bubbles aligned left (assistant) / right (user)
- Message bubble styles: user → `bg-slate-900 text-white rounded-br-sm`, assistant → `bg-slate-100 text-slate-700 rounded-bl-sm`
- Input row: `rounded-xl` input + `↑` send button with `hover:scale-105`
- Send wires user message + stub assistant reply ("⏳ AI responses will be available in Phase III.") to local state only — no API calls
- Enter key submits (Shift+Enter passes through)
- Dark mode: `dark:bg-zinc-900/90 dark:border-zinc-700/60`, bubbles, header, input all themed

**`ChatWidget.tsx`**
- `fixed bottom-6 right-6 z-50`
- Toggle button: `w-14 h-14 rounded-2xl backdrop-blur-md bg-slate-900/90 shadow-xl border border-white/20`
- Animations: `hover:scale-110 hover:shadow-2xl transition-all duration-200 ease-out`
- Panel entrance: `animate-in fade-in slide-in-from-bottom-4 duration-200`
- Icon: `✦` (closed) / `×` (open); button shifts to `bg-slate-700/90` when open
- Dark mode: `dark:bg-zinc-800/90 dark:border-zinc-700/60`

**`TasksView.tsx` — minimal change**
- Added `import ChatWidget from './ChatWidget'`
- Added `<ChatWidget />` before closing `</div>`, after all modals

## Outcome

- ✅ Impact: Floating AI chat button visible on the tasks page. Opens a glassmorphism panel with message bubbles, auto-scroll, and stubbed send. No backend calls. Existing todo logic untouched.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 2 created, 1 minimally updated.
- 🔁 Next prompts: Phase III — wire ChatPanel to AI API (streaming responses, system prompt with user's task list as context); add typing indicator animation.
- 🧠 Reflection: Keeping ChatPanel as a pure UI shell with local-state stubs is the right Phase III scaffold — easy to replace the stub with a real fetch/stream call without touching any other component.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add a typing indicator (animated dots) before the stub assistant reply appears
