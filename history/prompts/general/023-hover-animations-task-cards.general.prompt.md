---
id: 023
title: Hover Animations Task Cards
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Add subtle hover animations: hover:scale-[1.02], hover:shadow-2xl, transition duration-200 ease-out. Apply on task cards."
labels: ["frontend","ui","tailwind","animation","hover","refactor"]
links:
  spec: specs/ui/pages.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/components/TasksView.tsx (1 line changed)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Add subtle hover animations:

hover:scale-[1.02]
hover:shadow-2xl
transition duration-200 ease-out

Apply on task cards.

## Response snapshot

One targeted change to `components/TasksView.tsx` line 207. No other files touched.

**Change — TaskItem root div**

Appended three classes to the existing glassmorphism card element:

Before:
```tsx
<div className="flex items-center gap-3 px-4 py-3 rounded-2xl backdrop-blur-md bg-white/10 shadow-xl border border-white/20">
```
After:
```tsx
<div className="flex items-center gap-3 px-4 py-3 rounded-2xl backdrop-blur-md bg-white/10 shadow-xl border border-white/20 hover:scale-[1.02] hover:shadow-2xl transition duration-200 ease-out">
```

`transition duration-200 ease-out` animates both the scale and the shadow simultaneously.

## Outcome

- ✅ Impact: Each task card lifts 2% and deepens its shadow on hover with a smooth 200ms ease-out transition.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 1 file, 1 line changed.
- 🔁 Next prompts: Add a gradient page background to make the glass + lift effect more dramatic; add active:scale-[0.99] for a press-down feel.
- 🧠 Reflection: Smallest viable diff — three classes appended to the single element that defines card appearance. All behaviour, accessibility, and dark mode unchanged.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add active:scale-[0.99] for a subtle press feedback on click
