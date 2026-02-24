---
id: 024
title: SaaS Dashboard UI Refactor
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Refactor entire UI to modern SaaS dashboard style using Tailwind. Constraints: Minimal colors, Soft shadows, Rounded-xl elements, Clean spacing (p-6), Professional typography."
labels: ["frontend","ui","tailwind","saas","dashboard","refactor"]
links:
  spec: specs/ui/pages.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/app/globals.css (body bg updated to slate-50)
  - frontend/components/Header.tsx (full rewrite)
  - frontend/components/TasksView.tsx (full rewrite)
  - frontend/app/(auth)/sign-in/page.tsx (full rewrite)
  - frontend/app/(auth)/sign-up/page.tsx (full rewrite)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Refactor entire UI to modern SaaS dashboard style using Tailwind.

Constraints:
- Minimal colors
- Soft shadows
- Rounded-xl elements
- Clean spacing (p-6)
- Professional typography

## Response snapshot

Full UI refactor across 5 files establishing a consistent SaaS design system. Zero logic changes.

**Design system adopted:**

| Token | Light | Dark |
|-------|-------|------|
| Page bg | `bg-slate-50` | `dark:bg-zinc-900` |
| Card surface | `bg-white rounded-xl border border-gray-100 shadow-sm` | `dark:bg-zinc-800 dark:border-zinc-800` |
| Modal surface | `bg-white rounded-2xl shadow-lg border border-gray-100` | `dark:bg-zinc-800 dark:border-zinc-700` |
| Primary button | `bg-slate-900 rounded-lg` | `dark:bg-white dark:text-slate-900` |
| Secondary button | `border border-gray-200 rounded-lg` | `dark:border-zinc-600` |
| Heading | `font-semibold tracking-tight text-slate-900` | `dark:text-white` |
| Secondary text | `text-slate-500` / `text-xs` labels | `dark:text-zinc-400` |
| Focus ring | `focus:ring-slate-900` | `dark:focus:ring-zinc-400` |
| Input | `border-gray-200 rounded-lg` + placeholders | `dark:bg-zinc-700 dark:border-zinc-600` |

**Key decisions:**
- Dropped glassmorphism (`backdrop-blur-md bg-white/10`) — replaced with clean `bg-white` cards
- Primary accent switched from `blue-600` to `slate-900` (neutral, professional)
- Auth page headings changed to descriptive copy ("Welcome back" / "Create an account")
- Brand wordmark moved to small `tracking-widest uppercase` label above the headline
- Task count moved under heading as a subtitle (`text-sm text-slate-500`)
- Empty state boxed in a card (consistent with the card-heavy layout)
- Badge colours updated: `emerald-50/700` (completed) and `amber-50/700` (pending), with dark mode variants
- Edit/delete icon buttons given rounded-lg padding + contextual hover bg (slate / red)
- Toast changed from `bg-red-600` to `bg-slate-900` (neutral, less alarming for non-critical messages)
- Description truncation expanded from 40 → 60 chars (more content visible in wider cards)

## Outcome

- ✅ Impact: Full SaaS dashboard aesthetic across all pages — minimal palette, clean shadows, rounded-xl/2xl surfaces, professional typography. Dark mode preserved throughout.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 5 files rewritten. Zero logic changes.
- 🔁 Next prompts: Add a sidebar or stats bar; add keyboard shortcut (N) to open Add Task; add skeleton loading state.
- 🧠 Reflection: Replacing glassmorphism with clean whites is the right move for a SaaS dashboard — glass is a hero/landing page technique, not a data-dense UI pattern.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Add a thin indigo left-border accent to active/incomplete task cards for visual hierarchy
