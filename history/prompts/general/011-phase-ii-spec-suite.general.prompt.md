---
id: "011"
title: Phase II Spec Suite
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Create Phase II migration plan from console app to full-stack web app. Read @specs/constitution.md @specs/features/task-crud.md @specs/architecture.md. Create new specs: @specs/overview.md @specs/features/authentication.md @specs/api/rest-endpoints.md @specs/database/schema.md @specs/ui/pages.md. Requirements: Next.js 16 App Router, FastAPI backend, SQLModel ORM, Neon PostgreSQL, Better Auth JWT flow. Output detailed specs only. Do not implement code yet."
labels: ["phase-2","spec","authentication","rest-api","database","ui","nextjs","fastapi","sqlmodel","neon","better-auth","sdd"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/overview.md
  - specs/features/authentication.md
  - specs/api/rest-endpoints.md
  - specs/database/schema.md
  - specs/ui/pages.md
tests:
  - "Phase I invariant: uv run pytest tests/ -q — 107 passed (must not break)"
---

## Prompt

Create Phase II migration plan from console app to full-stack web app.

Read:
@specs/constitution.md
@specs/features/task-crud.md
@specs/architecture.md

Create new specs:

@specs/overview.md
@specs/features/authentication.md
@specs/api/rest-endpoints.md
@specs/database/schema.md
@specs/ui/pages.md

Requirements:
- Next.js 16 App Router
- FastAPI backend
- SQLModel ORM
- Neon PostgreSQL
- Better Auth JWT flow

Output detailed specs only.
Do not implement code yet.

## Response snapshot

Created 5 Phase II spec documents:

### specs/overview.md
- Goal statement: console → web, TaskManager unchanged
- Phase II stack table (Next.js 16, FastAPI, SQLModel, Neon, Better Auth)
- Migration principle table: Phase I module → Phase II replacement
- In-scope feature table (12 items) and explicit out-of-scope list
- Document hierarchy + precedence order
- Full repo structure (backend/ + frontend/ + Phase I src/ kept)
- SDD implementation sequence (10-step ordered workflow)
- Phase II success criteria (8 items, SC-P2-001 through SC-P2-008)
- 5 ADR candidates to document before implementation

### specs/features/authentication.md
- 4 user stories: sign-up (US-AUTH-01), sign-in (US-AUTH-02), sign-out (US-AUTH-03), protected routes (US-AUTH-04)
- 20 acceptance scenarios covering all happy paths and error paths
- Functional requirements FR-AUTH-001 through FR-AUTH-012
- Full error catalogue (9 entries)
- Auth flow diagram: browser → Next.js Better Auth → JWT → FastAPI JWT validation
- Better Auth config table (Next.js side + FastAPI side)
- Better Auth DB tables (user, session, account, verification)
- Route protection matrix (all routes with auth behaviour)
- Out-of-scope list (OAuth, magic link, MFA, RBAC, etc.)

### specs/api/rest-endpoints.md
- 6 endpoints: GET /api/tasks, POST /api/tasks, GET /api/tasks/{id}, PUT /api/tasks/{id}, DELETE /api/tasks/{id}, PATCH /api/tasks/{id}/toggle
- Full request/response contracts with example JSON for each endpoint
- Field-level constraints and validation rules
- Acceptance criteria per endpoint (27 criteria total)
- Error taxonomy table (7 status codes with conditions)
- Shared schemas: TaskRead, TaskCreate, TaskUpdate
- CORS configuration
- OpenAPI docs URLs
- Phase I CLI → Phase II REST mapping table

### specs/database/schema.md
- `task` table: 7 columns with types, constraints, and notes
- 4 Better Auth tables documented (user, session, account, verification)
- SQLModel schemas: Task (table=True), TaskCreate, TaskUpdate, TaskRead
- TaskStore DB adapter: interface contract (4 methods), constructor signature
- Update/toggle commit ownership model (route handler owns session.commit)
- Migration strategy: create_all() on startup; Alembic deferred
- Test DB strategy: SQLite StaticPool in-memory; dependency_overrides
- Environment variables for both backend/.env and frontend/.env.local
- Data integrity rules (6 rules with enforcement layer)

### specs/ui/pages.md
- App Router structure (full directory tree)
- Middleware route protection matrix
- 4 pages: / (redirect), /sign-in, /sign-up, /tasks
- ASCII layout mockups for sign-in, sign-up, and tasks pages
- Component hierarchy diagram (TasksView → Header, AddTaskButton, TaskList, TaskItem, etc.)
- Add Task form, Edit Task form, Delete confirmation dialog specs
- API client function table (5 functions)
- TypeScript types: Task, CreateTaskInput, UpdateTaskInput
- Error handling table (5 conditions → UI behaviours)
- Loading state table (5 actions → indicators)
- 8 UI success criteria (SC-UI-001 through SC-UI-008)
- Out-of-scope list (mobile, dark mode, drag-drop, etc.)

## Outcome

- ✅ Impact: Complete Phase II SDD spec suite; all 5 spec documents production-ready; no code written
- 🧪 Tests: Phase I invariant documented; no Phase II tests written yet (spec-only pass)
- 📁 Files: specs/overview.md, specs/features/authentication.md, specs/api/rest-endpoints.md, specs/database/schema.md, specs/ui/pages.md (all created)
- 🔁 Next prompts: Scaffold backend/ → write failing API tests (red) → implement routes (green)
- 🧠 Reflection: The TaskManager unchanged / TaskStore adapter pattern is the architectural linchpin — it means the entire Phase I service layer (44 unit tests) validates Phase II business logic for free. The DB adapter only needs integration tests for the SQL queries; the business rules are already proven.

## Evaluation notes (flywheel)

- Failure modes observed: none — all 5 spec documents created without blocking issues
- Graders run and results (PASS/FAIL): spec-only pass (no code to run)
- Prompt variant (if applicable): initial
- Next experiment: scaffold backend/ and run `uv run pytest backend/tests/` to validate the TaskManager reuse claim with a real SQLite test database
