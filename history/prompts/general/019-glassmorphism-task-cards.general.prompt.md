---
id: 019
title: Glassmorphism Task Cards Refactor
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Refactor task list UI using Tailwind glassmorphism style. Requirements: rounded-2xl, backdrop-blur-md, bg-white/10, shadow-xl, border border-white/20. Apply to task cards only."
labels: ["frontend","ui","tailwind","glassmorphism","refactor"]
links:
  spec: specs/ui/pages.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/components/TasksView.tsx (2 lines changed)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Refactor task list UI using Tailwind glassmorphism style.

Requirements:
- rounded-2xl
- backdrop-blur-md
- bg-white/10
- shadow-xl
- border border-white/20

Apply to task cards only.

## Response snapshot

Two targeted changes to `components/TasksView.tsx`. No other files touched.

**Change 1 — list container (line 141)**
Removed the shared `bg-white rounded-lg border divide-y` wrapper. Cards are
now independent elements, so the container becomes a neutral `flex flex-col gap-3`
spacer. The `divide-y` divider is no longer needed — each card's own border
provides visual separation.

Before:
```tsx
<div className="bg-white rounded-lg border divide-y">
```
After:
```tsx
<div className="flex flex-col gap-3">
```

**Change 2 — TaskItem root div (line 207)**
Added all five glassmorphism classes to the card element.

Before:
```tsx
<div className="flex items-center gap-3 px-4 py-3">
```
After:
```tsx
<div className="flex items-center gap-3 px-4 py-3 rounded-2xl backdrop-blur-md bg-white/10 shadow-xl border border-white/20">
```

Nothing else changed — modals, header, page background, buttons, and
typography are untouched.

## Outcome

- ✅ Impact: Each task renders as an independent glassmorphism card. The effect is most visible against a coloured or gradient page background; current bg-gray-50 gives a subtle result.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 1 file, 2 lines changed.
- 🔁 Next prompts: Add a gradient page background (e.g. bg-gradient-to-br) to make the glass effect visible; or adjust bg-white/10 opacity for the current light background.
- 🧠 Reflection: Smallest viable diff — only the two elements that define card appearance changed. All behaviour, accessibility, and spec compliance unchanged.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Change page background from bg-gray-50 to a gradient to make backdrop-blur-md visually apparent
