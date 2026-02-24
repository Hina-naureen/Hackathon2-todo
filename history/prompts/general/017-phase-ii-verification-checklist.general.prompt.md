---
id: 017
title: Phase II Verification Checklist
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: phase-ii
branch: master
user: pc
command: "Create Phase II verification checklist. Include: Backend API test steps, Frontend UI test steps, JWT auth verification, Neon database connection test, Signup → Create task → Logout → Login → Verify persistence flow"
labels: ["phase-ii","verification","checklist","e2e","testing","neon","jwt"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/phase2-verification-checklist.md (created)
tests:
  - n/a — checklist document, not code
---

## Prompt

Create Phase II verification checklist.

Include:
- Backend API test steps
- Frontend UI test steps
- JWT auth verification
- Neon database connection test
- Signup → Create task → Logout → Login → Verify persistence flow

## Response snapshot

Created `specs/phase2-verification-checklist.md` — a complete, runnable
Phase II verification guide with 7 sections:

0. Prerequisites (env files, service startup, automated suite)
1. Backend API Tests — 12 subsections with curl commands and expected responses
   for all 5 CRUD+toggle endpoints, auth guard (no/bad/expired token), validation
   errors, and user isolation
2. JWT Auth Verification — token structure, shared-secret round-trip, httpOnly
   cookie, AUTH_DISABLED flag
3. Neon Database Connection Test — Neon console setup, connection string,
   create_all verification, schema column check, persistence verification
4. Frontend UI Test Steps — 12 subsections covering sign-up/in/out, task CRUD,
   toggle optimistic UI, error handling
5. End-to-End Persistence Flow — 7-step scenario:
   Sign up → Create 3 tasks → Mutate state → Sign out → Sign in → Verify
   persistence → Verify user isolation
6. Success Criteria Summary — all 8 SC-P2-* criteria mapped to checklist sections
7. Known Limitations (out of scope for Phase II)

All expected values sourced directly from the spec files.
All `curl` and `python` commands are copy-paste runnable.

## Outcome

- ✅ Impact: Provides a complete verification guide that can be run top-to-bottom to confirm Phase II is production-ready before moving to Phase III.
- 🧪 Tests: Checklist references 144 automated tests (SC-P2-006) plus manual steps.
- 📁 Files: 1 created.
- 🔁 Next prompts: Work through the checklist top-to-bottom; if all items pass, Phase II is complete. Next is wiring a real Neon DATABASE_URL and finalizing BETTER_AUTH_SECRET.
- 🧠 Reflection: Spec-sourced expected values make the checklist authoritative — every step traces back to a spec section or SC-P2-* criterion.

## Evaluation notes (flywheel)

- Failure modes observed: n/a
- Graders run and results (PASS/FAIL): n/a
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run §0 prerequisites and §1 backend API tests
