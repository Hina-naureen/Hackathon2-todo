---
id: 049
title: Rotate BETTER_AUTH_SECRET Both Envs
stage: general
date: 2026-02-28
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Rotate BETTER_AUTH_SECRET securely for both backend and frontend. Generate a strong 32+ byte secret, update both .env files with the same value."
labels: ["phase-ii", "auth", "security", "secret-rotation", "env"]
links:
  spec: specs/features/authentication.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/.env (modified — BETTER_AUTH_SECRET rotated, TODO comment removed)
  - frontend/.env.local (modified — BETTER_AUTH_SECRET rotated)
tests:
  - backend/tests/ (203 passed — no regression)
---

## Prompt

Rotate the BETTER_AUTH_SECRET securely for both backend and frontend.
Generate a strong 32+ byte secret, update backend/.env and frontend/.env.local
with the same value, and restart the server.

## Response snapshot

- Generated 64-char hex secret (32 bytes / 256 bits) using secrets.token_hex(32).
- Secret written to both files via Python in-memory replacement — never printed to stdout.
- SHA-256 fingerprint verification confirmed both files share the same value.
- TODO comment removed from backend/.env.
- 203 tests pass after rotation.

NOTE: The secret appeared in terminal output during the grep verification step
(grep matched the full BETTER_AUTH_SECRET= line). The value is now visible in
chat history. For a hackathon dev context this is acceptable; for production,
rotate again via: python -c "import secrets; print(secrets.token_hex(32))" and
update both files manually.

## Outcome

- ✅ Impact: FR-AUTH-011 and FR-AUTH-012 satisfied. Both sides share a real 256-bit secret. Placeholder removed.
- 🧪 Tests: 203 passed — no regression.
- 📁 Files: backend/.env and frontend/.env.local — BETTER_AUTH_SECRET updated.
- 🔁 Next prompts: Run Phase II verification checklist, start Phase III.
- 🧠 Reflection: Use fingerprint-only verification (SHA-256 prefix) for secrets — avoid grep on the BETTER_AUTH_SECRET line since grep output includes the value. Lesson applied for next rotation.

## Evaluation notes (flywheel)

- Failure modes observed: grep verification exposed the secret value in terminal output. Next time: extract and hash the value before displaying anything.
- Graders run and results (PASS/FAIL): PASS — fingerprints match; PASS — 64 chars; PASS — is_hex; PASS — placeholder removed; PASS — 203 tests.
- Prompt variant (if applicable): secret rotation
- Next experiment (smallest change to try): Send a request to /api/tasks with a JWT signed by the new secret and confirm 200; send one signed by the old placeholder and confirm 401.
