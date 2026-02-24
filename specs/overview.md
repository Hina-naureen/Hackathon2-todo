# Phase II Overview — Full-Stack Web App

**Version:** 1.0.0
**Date:** 2026-02-24
**Status:** Planned
**Supersedes:** Phase I in-memory console app
**Constitution:** `.specify/memory/constitution.md`

---

## Goal

Migrate the Phase I in-memory Python console todo app into a production-ready
full-stack web application with persistent storage, user authentication, and a
modern React UI. The Phase I service layer (`TaskManager`) carries forward
**unchanged** — only the transport (CLI → REST) and storage (RAM → PostgreSQL)
are replaced.

---

## Phase II Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | Next.js App Router + TypeScript | 16 |
| **Backend** | FastAPI | 0.115+ |
| **ORM** | SQLModel | 0.0.21+ |
| **Database** | Neon DB (serverless PostgreSQL) | latest |
| **Authentication** | Better Auth | latest |
| **Package Manager (backend)** | UV | latest |
| **Package Manager (frontend)** | npm | latest |
| **Python** | 3.13+ | |
| **Node.js** | 22 LTS+ | |

Stack is **locked by constitution** — changes require an ADR + explicit user approval.

---

## Migration Principle

```
Phase I                         Phase II
-------                         --------
src/models.py (TaskStore)  →    SQLModel + Neon DB (TaskStore adapter)
src/task_manager.py        →    UNCHANGED (same class, same signatures)
src/cli.py                 →    FastAPI route handlers + Next.js UI
src/main.py (event loop)   →    FastAPI app + Uvicorn server
uv run todo                →    uv run uvicorn (backend) + next dev (frontend)
In-memory dict             →    PostgreSQL table (tasks)
No users                   →    Better Auth (email + password)
```

**Key invariant**: All 107 Phase I pytest tests must remain green throughout and
after Phase II scaffolding. `uv run todo` must still boot cleanly.

---

## Phase II Scope

### In Scope

| # | Feature | Spec |
|---|---------|------|
| 1 | User sign-up (email + password) | `specs/features/authentication.md` |
| 2 | User sign-in + session | `specs/features/authentication.md` |
| 3 | User sign-out | `specs/features/authentication.md` |
| 4 | Protected routes (UI + API) | `specs/features/authentication.md` |
| 5 | Create task (REST) | `specs/api/rest-endpoints.md` |
| 6 | List all tasks (REST) | `specs/api/rest-endpoints.md` |
| 7 | Update task (REST) | `specs/api/rest-endpoints.md` |
| 8 | Delete task (REST) | `specs/api/rest-endpoints.md` |
| 9 | Toggle complete/incomplete (REST) | `specs/api/rest-endpoints.md` |
| 10 | Task list UI | `specs/ui/pages.md` |
| 11 | Sign-in / sign-up UI | `specs/ui/pages.md` |
| 12 | Persistent storage (Neon DB) | `specs/database/schema.md` |

### Out of Scope (Phase II)

- Task sorting, filtering, or searching
- Task priorities, tags, or due dates
- OAuth / social sign-in (Google, GitHub, etc.)
- Email verification or password reset flows
- Real-time updates (WebSockets / SSE)
- AI features (deferred to Phase III)
- Containerisation / Kubernetes (deferred to Phase IV)
- File uploads or attachments

---

## Document Hierarchy (Precedence Order)

```
.specify/memory/constitution.md      ← highest — all-phase binding rules
specs/overview.md                    ← Phase II scope + migration contract (this file)
specs/features/authentication.md     ← auth user stories + acceptance criteria
specs/api/rest-endpoints.md          ← REST API contract (endpoints + schemas)
specs/database/schema.md             ← SQLModel + Neon DB table definitions
specs/ui/pages.md                    ← Next.js pages, routes, component contracts
```

If any lower document conflicts with a higher document, fix the lower document.

---

## Repository Structure

```
Hackathon2-todo/
│
├── backend/                          # FastAPI application (Phase II)
│   ├── src/
│   │   ├── main.py                   # FastAPI app entry
│   │   ├── models.py                 # SQLModel models + TaskStore adapter
│   │   ├── task_manager.py           # TaskManager (unchanged from Phase I)
│   │   ├── database.py               # Engine + session factory
│   │   ├── routes/
│   │   │   └── tasks.py              # Task CRUD + toggle route handlers
│   │   └── auth/
│   │       └── dependencies.py       # JWT bearer token validation
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_models.py
│   │   ├── test_task_manager.py      # Reused from Phase I — no changes needed
│   │   └── test_routes.py            # HTTP-level integration tests
│   ├── pyproject.toml
│   └── .env                          # DATABASE_URL, BETTER_AUTH_SECRET
│
├── frontend/                         # Next.js application (Phase II)
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── sign-in/page.tsx
│   │   │   └── sign-up/page.tsx
│   │   ├── (protected)/
│   │   │   └── tasks/page.tsx
│   │   ├── api/
│   │   │   └── auth/[...all]/route.ts
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── TaskList.tsx
│   │   ├── TaskForm.tsx
│   │   └── TaskItem.tsx
│   ├── lib/
│   │   ├── auth.ts                   # Better Auth config
│   │   └── api.ts                    # Typed fetch client for FastAPI
│   ├── middleware.ts                  # Route protection
│   ├── package.json
│   └── .env.local
│
├── src/                              # Phase I — kept intact, must still work
├── tests/                            # Phase I — all 107 tests must still pass
├── specs/                            # All specification documents
├── history/prompts/                  # PHRs
├── history/adr/                      # ADRs
├── CLAUDE.md
└── README.md
```

---

## SDD Implementation Sequence

No code is written until the spec for that step is complete and reviewed.

| Step | Action | Spec Gate |
|------|--------|-----------|
| 1 | Specs complete (this suite) | — |
| 2 | Scaffold `backend/` (UV, FastAPI, SQLModel, Neon) | `specs/database/schema.md` |
| 3 | Red: write failing API tests | `specs/api/rest-endpoints.md` |
| 4 | Green: implement TaskStore adapter + routes | `specs/api/rest-endpoints.md` |
| 5 | Integrate Better Auth JWT validation | `specs/features/authentication.md` |
| 6 | Scaffold `frontend/` (Next.js 16, Better Auth) | `specs/ui/pages.md` |
| 7 | Red: write failing component tests | `specs/ui/pages.md` |
| 8 | Green: implement pages + API client | `specs/ui/pages.md` |
| 9 | Integration test: full sign-in → CRUD → sign-out | all specs |
| 10 | Update `README.md`, `CLAUDE.md` | — |

---

## Success Criteria (Phase II)

| ID | Criterion |
|----|-----------|
| **SC-P2-001** | User can sign up, sign in, and sign out via the web UI. |
| **SC-P2-002** | All 5 task operations (add, view, update, delete, toggle) work via REST API with a valid token. |
| **SC-P2-003** | Tasks are persisted to Neon DB and survive a server restart. |
| **SC-P2-004** | Unauthenticated requests to `/api/tasks` return HTTP 401. |
| **SC-P2-005** | The task list UI reflects all task operations without a full page reload. |
| **SC-P2-006** | All 107 Phase I tests still pass (`uv run pytest tests/` from repo root). |
| **SC-P2-007** | `uv run todo` (Phase I console app) still boots and operates correctly. |
| **SC-P2-008** | No secrets are present in source code or committed to the repository. |

---

## ADRs to Document Before Implementation

| Decision | Significance |
|----------|-------------|
| Monorepo layout (`backend/` + `frontend/` in one repo) | Affects CI, deployment, and dev workflow |
| Better Auth JWT forwarding to FastAPI | Cross-cutting auth architecture |
| SQLite in-memory for backend unit tests | Test isolation strategy |
| `create_all()` over Alembic for Phase II migrations | Migration complexity vs YAGNI |
| TaskManager unchanged / TaskStore adapter bridge | Phase I → II service contract |
