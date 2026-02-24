---
id: 021
title: Status Badges Beside Task Title
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Add Tailwind status badges: Completed: bg-green-100 text-green-700. Pending: bg-yellow-100 text-yellow-700. Use small rounded-full badges beside task title."
labels: ["frontend","ui","tailwind","badges","refactor"]
links:
  spec: specs/ui/pages.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/components/TasksView.tsx (1 block changed)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Add Tailwind status badges: Completed: bg-green-100 text-green-700. Pending: bg-yellow-100 text-yellow-700. Use small rounded-full badges beside task title.

## Response snapshot

One block change inside `TaskItem` in `components/TasksView.tsx`. No other files touched.

Replaced the plain title `<p>` with a flex row containing the title `<span>` and a badge `<span>`:

```tsx
<div className="flex items-center gap-2 flex-wrap">
  <span className={`font-medium text-sm ${
    task.completed ? 'line-through text-gray-400' : 'text-gray-900'
  }`}>
    {task.title}
  </span>
  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
    task.completed ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
  }`}>
    {task.completed ? 'Completed' : 'Pending'}
  </span>
</div>
```

Badge colour changes reactively when the checkbox is toggled (completed/pending state).

## Outcome

- ✅ Impact: Each task card shows a coloured pill badge (Completed/Pending) inline with the title.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 1 file, 1 block changed.
- 🔁 Next prompts: Add dark mode variants; add gradient page background.
- 🧠 Reflection: Badge is driven by the same `task.completed` boolean used for the checkbox — zero additional state.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add dark mode counterparts bg-green-900/text-green-300 for dark completed badge
