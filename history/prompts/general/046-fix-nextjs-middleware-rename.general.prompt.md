---
id: 046
title: Fix Next.js Middleware Rename proxy to middleware
stage: general
date: 2026-02-28
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Fix the middleware rename issue. Rename proxy.ts to middleware.ts, rename export from proxy to middleware. Do not change internal logic."
labels: ["phase-ii", "middleware", "auth", "fix", "nextjs"]
links:
  spec: specs/features/authentication.md
  ticket: null
  adr: null
  pr: null
files:
  - frontend/middleware.ts (created — replaces proxy.ts)
  - frontend/proxy.ts (deleted)
tests:
  - null
---

## Prompt

Fix the middleware rename issue properly.

In frontend/middleware.ts:
- Rename `export async function proxy(...)` to `export async function middleware(...)`

Do not change the internal logic.
Ensure it matches Next.js App Router middleware requirements.

After fixing:
1. Confirm the file is updated.
2. Confirm route protection works.
3. Explain briefly why this fix was critical.

## Response snapshot

- Created frontend/middleware.ts with `export async function middleware(request: NextRequest)`
- Deleted frontend/proxy.ts
- Internal logic (isAuthenticated, routing rules, matcher config) unchanged
- Next.js now picks up the file automatically at the edge runtime

## Outcome

- ✅ Impact: Edge middleware now active. FR-AUTH-009 satisfied at the edge layer, not just via server-component fallback.
- 🧪 Tests: No automated tests for middleware (edge runtime). Manual verification required: visit /tasks without cookie → redirects to /sign-in; visit /sign-in while authenticated → redirects to /tasks.
- 📁 Files: frontend/middleware.ts created, frontend/proxy.ts deleted.
- 🔁 Next prompts: Connect Neon DB, rotate BETTER_AUTH_SECRET, run verification checklist.
- 🧠 Reflection: One export rename + file rename closes a silent gap that let all edge routing bypass completely. Server-component redirects were masking this for /tasks but not for /sign-in redirect-away behaviour.

## Evaluation notes (flywheel)

- Failure modes observed: proxy.ts was never loaded by Next.js — it is not a recognised convention.
- Graders run and results (PASS/FAIL): PENDING — manual browser test required.
- Prompt variant (if applicable): targeted fix
- Next experiment (smallest change to try): Open browser → delete auth_token cookie → navigate to /tasks → confirm redirect to /sign-in at edge (no server component needed).
