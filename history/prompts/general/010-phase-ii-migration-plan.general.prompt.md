---
id: "010"
title: Phase II Migration Plan
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Create Phase II migration plan. Goal: Transform Phase I console todo into Full-Stack Web App. Output: Required new specs, Folder changes, API layer plan, Database schema plan, Auth integration plan"
labels: ["phase-2","migration","plan","fastapi","nextjs","sqlmodel","neon","better-auth","architecture"]
links:
  spec: specs/architecture.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/phase2-migration-plan.md
tests:
  - "Phase I: uv run pytest tests/ -q — 107 passed (invariant: must not break)"
---

## Prompt

Create Phase II migration plan.
Goal: Transform Phase I console todo into Full-Stack Web App.
Output: Required new specs, Folder changes, API layer plan, Database schema plan, Auth integration plan

## Response snapshot

Created `specs/phase2-migration-plan.md` — a complete Phase II migration reference document.

Structure:

1. **Stack summary** — Next.js 15 (App Router), FastAPI, SQLModel, Neon DB, Better Auth
2. **Required new specs** — 6 spec documents to write before any code (auth.md, task-api.md, architecture-phase2.md, phase2-api/{spec,plan,tasks}.md), with authoring order
3. **Folder structure changes** — side-by-side Phase I vs Phase II layout; backend/ and frontend/ monorepo; Phase I src/ and tests/ kept intact
4. **API layer plan** — 6 REST endpoints (GET/POST/PUT/DELETE /api/tasks, PATCH /api/tasks/{id}/toggle), full request/response contracts, error taxonomy, dependency injection pattern with `get_current_user` and `get_session`
5. **Database schema plan** — SQLModel `Task` model (user_id, timestamps), `TaskStore` DB adapter (same interface as Phase I, constructor-injectable), Neon DB connection setup, migration strategy (`create_all()`, Alembic deferred)
6. **Auth integration plan** — Better Auth on Next.js (sign-in/sign-up, session, catch-all route), middleware.ts for route protection, `tasksApi` typed client forwarding Bearer token, JWT validation via PyJWT in FastAPI with shared `BETTER_AUTH_SECRET`
7. **Implementation sequence** — 13-step ordered workflow following SDD lifecycle
8. **ADR candidates** — 5 decisions to document before architecture spec
9. **Invariants** — 107 Phase I tests must still pass; `uv run todo` must still boot; `task_manager.py` must not be modified

Key architectural insight: `TaskManager` carries forward completely unchanged. Only `TaskStore` is replaced with a DB-backed adapter (same public interface, constructor-injected session + user_id). This preserves all 107 Phase I tests and the validated service contract.

## Outcome

- ✅ Impact: Complete Phase II blueprint; service layer reuse confirmed; all 5 requested output areas covered
- 🧪 Tests: Phase I invariant documented (107 tests must still pass after scaffold)
- 📁 Files: specs/phase2-migration-plan.md (created)
- 🔁 Next prompts: Write specs/features/auth.md → specs/features/task-api.md → specs/architecture-phase2.md → scaffold backend/
- 🧠 Reflection: The Phase I three-layer separation pays off here — TaskManager needs zero changes because the store interface was cleanly separated from the business logic. The DB adapter pattern is the only structural change needed at the data layer.

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): Phase I pytest invariant documented; no Phase II code written yet
- Prompt variant (if applicable): initial
- Next experiment: write specs/features/auth.md and confirm Better Auth + FastAPI JWT strategy before scaffolding
