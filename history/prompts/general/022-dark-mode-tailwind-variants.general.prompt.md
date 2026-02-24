---
id: 022
title: Dark Mode Tailwind Variants
stage: refactor
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: frontend
branch: master
user: pc
command: "Enable dark mode styling. Use Tailwind dark: variants: dark:bg-zinc-900, dark:text-white, dark:border-zinc-700. Do not change logic, UI only."
labels: ["frontend","ui","tailwind","dark-mode","refactor"]
links:
  spec: specs/ui/pages.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/app/globals.css (dark media query added)
  - frontend/components/Header.tsx (dark: variants added)
  - frontend/components/TasksView.tsx (dark: variants added — page, task items, modals)
  - frontend/app/(auth)/sign-in/page.tsx (dark: variants added)
  - frontend/app/(auth)/sign-up/page.tsx (dark: variants added)
tests:
  - npm run build — production build passes cleanly
---

## Prompt

Enable dark mode styling. Use Tailwind dark: variants: dark:bg-zinc-900, dark:text-white, dark:border-zinc-700. Do not change logic, UI only.

## Response snapshot

Additive-only UI changes across 5 files. No logic, no structure, no behaviour changed.

**Strategy:** Tailwind v4 uses `prefers-color-scheme: dark` media strategy by default — `dark:` variants apply automatically when the OS is in dark mode. No `class="dark"` toggle or layout changes needed.

**`globals.css`**
Added `@media (prefers-color-scheme: dark)` block overriding body background (`#18181b` = zinc-900) and text (`#fafafa`). Required because the body's inline CSS would otherwise override Tailwind's dark utilities.

**`Header.tsx`**
- `header`: added `dark:bg-zinc-900 dark:border-zinc-700`
- App name span: added `dark:text-white`
- Email span: added `dark:text-zinc-400`
- Sign Out button: added `dark:text-zinc-400 dark:hover:text-white dark:border-zinc-700 dark:hover:bg-zinc-800`

**`sign-in/page.tsx` and `sign-up/page.tsx`** (same pattern)
- Page wrapper: `dark:bg-zinc-900`
- Heading h1/h2: `dark:text-white`
- Card div: `dark:bg-zinc-800 dark:border-zinc-700`
- Labels: `dark:text-zinc-300`
- Inputs: `dark:bg-zinc-700 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-400`
- Footer text: `dark:text-zinc-400`

**`TasksView.tsx`**
- Page wrapper: `dark:bg-zinc-900`
- "My Tasks" heading: `dark:text-white`
- Empty state / task count text: `dark:text-zinc-400`
- Task title span (incomplete): `dark:text-white`; (complete): `dark:text-zinc-500`
- Task description: `dark:text-zinc-400`
- Edit/delete icon buttons: `dark:text-zinc-500`, hover `dark:hover:text-blue-400` / `dark:hover:text-red-400`
- TaskFormModal card: `dark:bg-zinc-800 dark:border-zinc-700`
- Modal heading: `dark:text-white`
- Modal close button: `dark:text-zinc-500 dark:hover:text-zinc-300`
- Form labels: `dark:text-zinc-300`
- Form inputs: `dark:bg-zinc-700 dark:border-zinc-700 dark:text-white dark:placeholder:text-zinc-400`
- Cancel button: `dark:text-zinc-400 dark:border-zinc-700 dark:hover:bg-zinc-700`
- DeleteModal card: `dark:bg-zinc-800 dark:border-zinc-700`
- DeleteModal headings/text: `dark:text-white` / `dark:text-zinc-300` / `dark:text-zinc-400`
- DeleteModal cancel button: same as TaskFormModal cancel

## Outcome

- ✅ Impact: All pages (sign-in, sign-up, tasks, header) respond to OS dark mode preference with zinc-900 backgrounds, white/zinc text, and zinc-700 borders. No logic changed.
- 🧪 Tests: npm run build — compiled successfully, TypeScript clean.
- 📁 Files: 5 files, additive dark: variants only.
- 🔁 Next prompts: Add gradient page background to make glassmorphism backdrop-blur-md visible in dark mode; add dark mode badge variants (bg-green-900/text-green-300).
- 🧠 Reflection: Additive-only approach — every existing class is preserved, dark: counterparts appended. Zero risk of breaking light mode.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): npm run build PASS
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Switch page background from bg-gray-50/dark:bg-zinc-900 to a gradient to make backdrop-blur-md visually apparent in both modes
