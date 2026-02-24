# Phase II Migration Plan — Console → Full-Stack Web App

**Date**: 2026-02-24
**Status**: Planned
**Author**: Claude Code (claude-sonnet-4-6)
**Constitution**: `.specify/memory/constitution.md`
**Phase I Base**: `specs/architecture.md`

---

## Goal

Transform the Phase I in-memory Python console todo app into a full-stack web
application. The service layer (`TaskManager`) carries forward unchanged.
Only the transport (CLI) and storage (in-memory) are replaced.

---

## Phase II Stack (Constitution-Locked)

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 15 (App Router) + TypeScript |
| **Backend** | FastAPI + Python 3.13 |
| **ORM** | SQLModel |
| **Database** | Neon DB (PostgreSQL, serverless) |
| **Authentication** | Better Auth (Next.js) + JWT validation (FastAPI) |
| **Package Manager** | UV (backend) · npm / bun (frontend) |

---

## 1. Required New Specs

Create these spec documents **before writing any code** (SDD rule: no code without a spec).

| # | File | Stage | Purpose |
|---|------|-------|---------|
| 1 | `specs/features/auth.md` | spec | User stories for sign-up, sign-in, sign-out, protected routes |
| 2 | `specs/features/task-api.md` | spec | REST API contract for task CRUD (US-01–US-05, HTTP transport) |
| 3 | `specs/phase2-api/spec.md` | spec | Phase II overall feature set and acceptance criteria |
| 4 | `specs/phase2-api/plan.md` | plan | Phase II architecture decisions, ADR links |
| 5 | `specs/phase2-api/tasks.md` | tasks | Testable task breakdown for Phase II implementation |
| 6 | `specs/architecture-phase2.md` | plan | Updated architecture spec (replaces Phase I architecture.md scope) |

### Spec authoring order

```
specs/features/auth.md
    ↓
specs/features/task-api.md
    ↓
specs/architecture-phase2.md
    ↓
specs/phase2-api/spec.md → plan.md → tasks.md
```

---

## 2. Folder Structure Changes

### Phase I (current)

```
Hackathon2-todo/
├── src/
│   ├── main.py
│   ├── models.py
│   ├── task_manager.py
│   └── cli.py
├── tests/
├── specs/
├── pyproject.toml
└── ...
```

### Phase II (target)

```
Hackathon2-todo/
│
├── backend/                          # FastAPI application
│   ├── src/
│   │   ├── main.py                   # FastAPI app + Uvicorn entry
│   │   ├── models.py                 # SQLModel models (replaces in-memory models)
│   │   ├── task_manager.py           # TaskManager (UNCHANGED from Phase I)
│   │   ├── database.py               # Engine + session factory (Neon DB)
│   │   ├── routes/
│   │   │   └── tasks.py              # CRUD + toggle route handlers
│   │   └── auth/
│   │       └── dependencies.py       # JWT bearer token validator
│   ├── tests/
│   │   ├── conftest.py               # DB test fixtures (SQLite in-memory)
│   │   ├── test_models.py
│   │   ├── test_task_manager.py      # Reused from Phase I (unchanged)
│   │   └── test_routes.py            # HTTP route integration tests
│   ├── pyproject.toml                # UV config + FastAPI deps
│   └── .env                          # DATABASE_URL, JWT_SECRET (gitignored)
│
├── frontend/                         # Next.js application
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── sign-in/page.tsx
│   │   │   └── sign-up/page.tsx
│   │   ├── (protected)/
│   │   │   └── tasks/page.tsx        # Main todo UI (requires auth)
│   │   ├── api/
│   │   │   └── auth/
│   │   │       └── [...all]/route.ts # Better Auth catch-all handler
│   │   ├── layout.tsx
│   │   └── page.tsx                  # Public landing / redirect
│   ├── components/
│   │   ├── TaskList.tsx
│   │   ├── TaskForm.tsx
│   │   └── TaskItem.tsx
│   ├── lib/
│   │   ├── auth.ts                   # Better Auth server + client config
│   │   └── api.ts                    # Typed FastAPI client (fetch wrapper)
│   ├── middleware.ts                  # Route protection (Better Auth session)
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.local                    # BETTER_AUTH_SECRET, API_URL (gitignored)
│
├── src/                              # Phase I source (kept; not deleted)
├── tests/                            # Phase I tests (kept; all 107 still pass)
│
├── specs/
│   ├── constitution.md               # Phase I rules (kept)
│   ├── architecture.md               # Phase I architecture (kept as historical)
│   ├── architecture-phase2.md        # NEW — Phase II architecture
│   ├── features/
│   │   ├── task-crud.md              # Phase I spec (kept)
│   │   ├── task-api.md               # NEW — REST API version
│   │   └── auth.md                   # NEW — authentication
│   └── phase2-api/
│       ├── spec.md                   # NEW
│       ├── plan.md                   # NEW
│       └── tasks.md                  # NEW
│
├── history/
│   ├── prompts/                      # PHRs accumulate here
│   └── adr/                          # ADRs (Phase II will have several)
│
├── .specify/
│   ├── memory/constitution.md        # Global constitution
│   └── templates/
│
├── CLAUDE.md                         # Updated for Phase II workflow
└── README.md                         # Updated for Phase II setup
```

---

## 3. API Layer Plan (FastAPI)

### Application entry: `backend/src/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.tasks import router as tasks_router

app = FastAPI(title="Todo API - Phase II", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], ...)
app.include_router(tasks_router, prefix="/api/tasks", tags=["tasks"])
```

Run command: `uv run uvicorn src.main:app --reload`

---

### REST endpoints: `backend/src/routes/tasks.py`

All routes require a valid Bearer token (Better Auth JWT).

| Method | Path | Description | Phase I equivalent |
|--------|------|-------------|-------------------|
| `GET` | `/api/tasks` | List all tasks for authenticated user | `handle_view` |
| `POST` | `/api/tasks` | Create a new task | `handle_add` |
| `GET` | `/api/tasks/{id}` | Get a single task | `TaskManager.get_task` |
| `PUT` | `/api/tasks/{id}` | Update title and/or description | `handle_update` |
| `DELETE` | `/api/tasks/{id}` | Delete task with confirmation | `handle_delete` |
| `PATCH` | `/api/tasks/{id}/toggle` | Toggle complete/incomplete | `handle_toggle` |

---

### Request / Response contracts

#### `POST /api/tasks`

```
Request body:
  { "title": "string (required, max 200)", "description": "string (optional, max 500)" }

Response 201:
  { "id": 1, "title": "...", "description": "...", "completed": false }

Response 422:
  { "detail": [{ "loc": ["body","title"], "msg": "Title cannot be empty." }] }
```

#### `PUT /api/tasks/{id}`

```
Request body:
  { "title": "string | null", "description": "string | null" }
  null → keep existing value  (same Enter-to-keep semantics as Phase I)

Response 200: updated task object
Response 404: { "detail": "Task #<id> not found." }
```

#### `PATCH /api/tasks/{id}/toggle`

```
Response 200: { "id": ..., "completed": true/false, ... }
Response 404: { "detail": "Task #<id> not found." }
```

---

### Error taxonomy

| HTTP Status | Condition |
|-------------|-----------|
| `400 Bad Request` | Validation failure (empty title, length exceeded) |
| `401 Unauthorized` | Missing or invalid Bearer token |
| `404 Not Found` | Task ID does not exist |
| `422 Unprocessable Entity` | Pydantic / SQLModel schema validation failure |
| `500 Internal Server Error` | Unexpected DB or application error |

---

### Dependency injection pattern

```python
# backend/src/auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer()

async def get_current_user(token = Depends(bearer_scheme)) -> str:
    """Validate Better Auth JWT; return user_id or raise 401."""
    user_id = verify_jwt(token.credentials)  # decode + check exp + secret
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
    return user_id

# Usage in route:
@router.get("/")
async def list_tasks(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    manager = TaskManager(TaskStore(session, user_id))
    return manager.get_all_tasks()
```

---

## 4. Database Schema Plan (SQLModel + Neon DB)

### Connection: `backend/src/database.py`

```python
from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.environ["DATABASE_URL"]  # Neon DB connection string from .env
engine = create_engine(DATABASE_URL, echo=False)

def get_session():
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
```

---

### SQLModel schema: `backend/src/models.py`

```python
from datetime import datetime
from sqlmodel import Field, SQLModel

class TaskBase(SQLModel):
    title: str = Field(max_length=200)
    description: str = Field(default="", max_length=500)
    completed: bool = Field(default=False)

class Task(TaskBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)           # Better Auth user ID
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class TaskCreate(TaskBase):
    pass                                        # Input schema (no id, no timestamps)

class TaskUpdate(SQLModel):
    title: str | None = None
    description: str | None = None             # null = keep existing

class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime                        # Output schema (no user_id exposed)
```

---

### Database migration strategy

Phase II uses **table creation** (not Alembic) for initial setup — `SQLModel.metadata.create_all(engine)`.

| Action | Command |
|--------|---------|
| Create tables | `uv run python -c "from src.database import create_db_and_tables; create_db_and_tables()"` |
| Drop and recreate (dev only) | `uv run python -c "from src.database import *; SQLModel.metadata.drop_all(engine); create_db_and_tables()"` |

Full Alembic migrations are deferred to Phase III+ (constitution: YAGNI).

---

### TaskStore adapter (Phase I → Phase II bridge)

`TaskManager` is unchanged. The `TaskStore` is replaced with a DB-backed adapter:

```python
# backend/src/models.py (TaskStore adapter)

class TaskStore:
    """DB-backed TaskStore — same interface as Phase I in-memory TaskStore."""

    def __init__(self, session: Session, user_id: str) -> None:
        self._session = session
        self._user_id = user_id

    def add(self, title: str, description: str = "") -> Task:
        task = Task(title=title, description=description, user_id=self._user_id)
        self._session.add(task)
        self._session.commit()
        self._session.refresh(task)
        return task

    def get_all(self) -> list[Task]:
        return self._session.exec(
            select(Task).where(Task.user_id == self._user_id)
        ).all()

    def get_by_id(self, task_id: int) -> Task | None:
        return self._session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == self._user_id)
        ).first()

    def delete(self, task_id: int) -> bool:
        task = self.get_by_id(task_id)
        if not task:
            return False
        self._session.delete(task)
        self._session.commit()
        return True
```

`TaskManager` receives this adapter via constructor injection — **zero changes to `task_manager.py`**.

---

### Neon DB setup

1. Create a project at [neon.tech](https://neon.tech)
2. Copy the connection string from the dashboard
3. Set in `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<db>?sslmode=require
```

4. Add `python-dotenv` as a dev dep; load `.env` at startup via `load_dotenv()`.

---

## 5. Auth Integration Plan (Better Auth + Next.js)

### Architecture

```
Browser
  │
  ├── GET  /tasks         → Next.js (protected, middleware checks session)
  ├── POST /api/auth/*    → Better Auth handlers (sign-in / sign-up / sign-out)
  └── GET/POST/PUT/... /api/tasks/* → FastAPI (validates Bearer token)
                                           ↑
                              Better Auth JWT (forwarded by Next.js fetch)
```

---

### Better Auth setup: `frontend/lib/auth.ts`

```typescript
import { betterAuth } from "better-auth";
import { db } from "./db";  // Better Auth DB adapter (or use built-in)

export const auth = betterAuth({
  database: {
    provider: "pg",
    url: process.env.DATABASE_URL!,   // Same Neon DB (separate auth tables)
  },
  emailAndPassword: { enabled: true },
  secret: process.env.BETTER_AUTH_SECRET!,
  baseURL: process.env.NEXT_PUBLIC_APP_URL!,
});

export const { signIn, signUp, signOut, useSession } = auth;
```

Catch-all route: `frontend/app/api/auth/[...all]/route.ts`

```typescript
import { auth } from "@/lib/auth";
import { toNextJsHandler } from "better-auth/next-js";
export const { GET, POST } = toNextJsHandler(auth);
```

---

### Route protection: `frontend/middleware.ts`

```typescript
import { auth } from "@/lib/auth";
import { NextRequest, NextResponse } from "next/server";

export default async function middleware(req: NextRequest) {
  const session = await auth.api.getSession({ headers: req.headers });
  const protectedPaths = ["/tasks"];

  if (!session && protectedPaths.some(p => req.nextUrl.pathname.startsWith(p))) {
    return NextResponse.redirect(new URL("/sign-in", req.url));
  }
  return NextResponse.next();
}

export const config = { matcher: ["/tasks/:path*"] };
```

---

### Forwarding token to FastAPI: `frontend/lib/api.ts`

```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL!;  // http://localhost:8000

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  session: { token: string },
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${session.token}`,
      ...options.headers,
    },
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const tasksApi = {
  list:   (s) => apiRequest<Task[]>("/api/tasks", {}, s),
  create: (s, body) => apiRequest<Task>("/api/tasks", { method: "POST", body: JSON.stringify(body) }, s),
  update: (s, id, body) => apiRequest<Task>(`/api/tasks/${id}`, { method: "PUT", body: JSON.stringify(body) }, s),
  delete: (s, id) => apiRequest<void>(`/api/tasks/${id}`, { method: "DELETE" }, s),
  toggle: (s, id) => apiRequest<Task>(`/api/tasks/${id}/toggle`, { method: "PATCH" }, s),
};
```

---

### Better Auth tables (auto-created in Neon DB)

Better Auth creates its own tables in the same Neon DB instance:

| Table | Contents |
|-------|----------|
| `user` | id, name, email, emailVerified, image |
| `session` | id, userId, token, expiresAt |
| `account` | id, userId, provider, providerAccountId |
| `verification` | id, identifier, value, expiresAt |

The `Task.user_id` column references `user.id` from Better Auth — no foreign key constraint in Phase II (YAGNI), but the value is set from the validated JWT payload.

---

### JWT validation in FastAPI: `backend/src/auth/dependencies.py`

Better Auth issues standard JWT tokens. FastAPI validates them using the shared secret:

```python
import jwt  # PyJWT
import os

SECRET = os.environ["BETTER_AUTH_SECRET"]

def verify_jwt(token: str) -> str | None:
    try:
        payload = jwt.decode(token, SECRET, algorithms=["HS256"])
        return payload.get("sub")          # user_id
    except jwt.PyJWTError:
        return None
```

`.env` on both sides must share the same `BETTER_AUTH_SECRET` value.

---

## 6. Implementation Sequence

Follow SDD lifecycle for each step — spec before code.

```
Step 1  Write specs/features/auth.md
Step 2  Write specs/features/task-api.md
Step 3  Write specs/architecture-phase2.md
Step 4  Scaffold backend/ (FastAPI + UV + SQLModel + Neon DB)
Step 5  Write failing tests for API routes (red)
Step 6  Implement TaskStore DB adapter (green)
Step 7  Implement FastAPI routes (green)
Step 8  Scaffold frontend/ (Next.js + Better Auth)
Step 9  Write failing tests for frontend components (red)
Step 10 Implement frontend pages + API client (green)
Step 11 Integration test: full sign-in → CRUD → sign-out flow
Step 12 Update README.md for Phase II setup
Step 13 Update CLAUDE.md for Phase II workflow
```

---

## 7. ADRs to Create

| Decision | Trigger |
|----------|---------|
| **Monorepo vs polyrepo** | backend/ + frontend/ in same repo |
| **Better Auth JWT forwarding** | Chosen over session cookie forwarding to FastAPI |
| **SQLite for tests vs Neon test branch** | `StaticPool` SQLite for unit speed vs Neon test branch for integration fidelity |
| **No Alembic for Phase II** | `create_all()` sufficient; Alembic deferred to Phase III |
| **TaskManager unchanged** | Phase I service layer reused verbatim as Phase II contract |

Suggest each with `/sp.adr <title>` before writing the architecture spec.

---

## 8. Invariants (Must Not Break)

- All 107 Phase I tests must still pass after Phase II scaffold (`uv run pytest tests/` from root).
- `uv run todo` (Phase I console app) must still boot cleanly.
- `task_manager.py` must not be modified — it is the verified service contract.
- No secrets in source code. All credentials via `.env` / `.env.local`.
- Constitution stack is locked — no substitutions without ADR + user approval.

---

## References

| Document | Path |
|----------|------|
| Global constitution | `.specify/memory/constitution.md` |
| Phase I constitution | `specs/constitution.md` |
| Phase I architecture | `specs/architecture.md` |
| Phase I feature spec | `specs/features/task-crud.md` |
| Phase I service layer | `src/task_manager.py` |
| Phase I data layer | `src/models.py` |
