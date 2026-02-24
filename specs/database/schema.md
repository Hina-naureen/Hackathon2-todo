# Database Specification: Schema — Phase II

**Version:** 1.0.0
**Date:** 2026-02-24
**Status:** Draft
**Stage:** spec
**Phase:** II
**ORM:** SQLModel 0.0.21+
**Database:** Neon DB (serverless PostgreSQL)
**Overview:** `specs/overview.md`
**Constitution:** `.specify/memory/constitution.md`

---

## Overview

Phase II introduces persistent storage via **Neon DB** (serverless PostgreSQL)
managed through the **SQLModel** ORM. The in-memory `TaskStore` (Phase I) is
replaced by a DB-backed adapter that exposes the identical public interface,
allowing `TaskManager` to remain completely unchanged.

Better Auth manages its own user-related tables in the same Neon DB instance.

---

## Database Connection

| Setting | Value |
|---------|-------|
| Provider | Neon DB (serverless PostgreSQL) |
| SSL | Required (`sslmode=require`) |
| Driver | `psycopg2` (sync) |
| Connection string env var | `DATABASE_URL` |
| Location | `backend/.env` (never committed to git) |

**Connection string format:**

```
postgresql+psycopg2://<user>:<password>@<host>.neon.tech/<db>?sslmode=require
```

---

## Tables

### Application Tables (SQLModel-managed)

#### `task`

Stores all todo tasks. Every row belongs to exactly one user.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | `PRIMARY KEY`, auto-increment | Unique task identifier |
| `title` | `VARCHAR(200)` | `NOT NULL` | Task title, 1–200 chars |
| `description` | `VARCHAR(500)` | `NOT NULL`, default `''` | Optional description |
| `completed` | `BOOLEAN` | `NOT NULL`, default `FALSE` | Completion flag |
| `user_id` | `VARCHAR` | `NOT NULL`, indexed | Better Auth user UUID |
| `created_at` | `TIMESTAMP` | `NOT NULL`, default `NOW()` | Row creation time (UTC) |
| `updated_at` | `TIMESTAMP` | `NOT NULL`, default `NOW()` | Last modification time (UTC) |

**Index:** `idx_task_user_id` on `user_id` — all queries filter by user.

**Notes:**
- No foreign key constraint on `user_id` → `user.id` in Phase II (YAGNI).
  This avoids cascade complexity; referential integrity is enforced by the
  application layer (the JWT `sub` claim is always a valid user ID).
- `updated_at` is updated by the application layer on every `update_task` and
  `toggle_complete` call — not by a DB trigger in Phase II.

---

### Auth Tables (Better Auth-managed)

Better Auth creates and owns these tables via its own schema migration on first
run. **Do not modify these tables manually.**

#### `user`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `VARCHAR` | UUID (primary key) |
| `name` | `VARCHAR` | Display name |
| `email` | `VARCHAR` | Unique email address |
| `emailVerified` | `BOOLEAN` | Email verification status |
| `image` | `VARCHAR` | Profile image URL (nullable) |
| `createdAt` | `TIMESTAMP` | Account creation time |
| `updatedAt` | `TIMESTAMP` | Last update time |

#### `session`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `VARCHAR` | Session ID (primary key) |
| `userId` | `VARCHAR` | FK → `user.id` |
| `token` | `VARCHAR` | JWT token value |
| `expiresAt` | `TIMESTAMP` | Session expiry |
| `ipAddress` | `VARCHAR` | Client IP (nullable) |
| `userAgent` | `VARCHAR` | Client user agent (nullable) |
| `createdAt` | `TIMESTAMP` | |
| `updatedAt` | `TIMESTAMP` | |

#### `account`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `VARCHAR` | (primary key) |
| `userId` | `VARCHAR` | FK → `user.id` |
| `accountId` | `VARCHAR` | Provider account ID |
| `providerId` | `VARCHAR` | `"credential"` for email/password |
| `password` | `VARCHAR` | Argon2/bcrypt hash (nullable for OAuth) |
| `createdAt` | `TIMESTAMP` | |
| `updatedAt` | `TIMESTAMP` | |

#### `verification`

| Column | Type | Description |
|--------|------|-------------|
| `id` | `VARCHAR` | (primary key) |
| `identifier` | `VARCHAR` | Email address |
| `value` | `VARCHAR` | Verification token |
| `expiresAt` | `TIMESTAMP` | Token expiry |

---

## SQLModel Schemas

### `Task` (table model)

```
class Task(SQLModel, table=True):
    id:          Optional[int]  — primary key, auto-increment
    title:       str            — max_length=200
    description: str            — max_length=500, default=""
    completed:   bool           — default=False
    user_id:     str            — indexed, NOT NULL
    created_at:  datetime       — default=utcnow
    updated_at:  datetime       — default=utcnow
```

### `TaskCreate` (input schema — POST /api/tasks)

```
class TaskCreate(SQLModel):
    title:       str            — required, 1–200 chars
    description: str            — optional, 0–500 chars, default=""
```

No `id`, `completed`, `user_id`, or timestamps — the server sets all of these.

### `TaskUpdate` (input schema — PUT /api/tasks/{id})

```
class TaskUpdate(SQLModel):
    title:       Optional[str]  — null = keep existing; "" = validation error
    description: Optional[str]  — null = keep existing; "" = clear description
```

Both fields are optional. An empty request body results in no changes.

### `TaskRead` (output schema — all task responses)

```
class TaskRead(SQLModel):
    id:          int
    title:       str
    description: str
    completed:   bool
    created_at:  datetime
    updated_at:  datetime
```

`user_id` is **excluded** from all API responses.

---

## TaskStore DB Adapter

The DB adapter replaces Phase I's `dict[int, Task]` backing store while
preserving the exact same public interface, enabling `TaskManager` to work
without any changes.

### Interface contract (identical to Phase I)

| Method | Signature | Behaviour |
|--------|-----------|-----------|
| `add` | `(title, description) → Task` | Insert row; return with auto-assigned `id` |
| `get_all` | `() → list[Task]` | SELECT all rows for `user_id`, ordered by `id` ASC |
| `get_by_id` | `(task_id) → Task \| None` | SELECT by `id` AND `user_id`; return `None` if missing |
| `delete` | `(task_id) → bool` | DELETE by `id` AND `user_id`; return `True` if deleted, `False` if not found |

### Constructor

```
TaskStore(session: Session, user_id: str) → TaskStore
```

The `Session` is a FastAPI-injected SQLModel session scoped to the request.
The `user_id` is extracted from the validated JWT `sub` claim.

### Update and toggle

`update_task` and `toggle_complete` in `TaskManager` mutate the `Task` object
returned by `get_by_id`. The DB adapter must ensure that mutations to the
returned object are flushed to the database. This is achieved by:

1. `get_by_id` returns the live SQLModel ORM object (not a copy).
2. After `TaskManager` mutates the object, the route handler calls
   `session.commit()` and `session.refresh(task)` before returning.

The route handler owns the commit — `TaskManager` and `TaskStore` never call
`session.commit()` directly. This keeps the service layer DB-agnostic.

---

## Migration Strategy

### Phase II initial setup

Use `SQLModel.metadata.create_all(engine)` called once at application startup.
This creates all `SQLModel, table=True` tables if they do not already exist.
It does not modify existing tables.

Run command:

```bash
uv run python -c "from src.database import create_db_and_tables; create_db_and_tables()"
```

### Development reset (destructive — dev only)

```bash
uv run python -c "
from src.database import engine, create_db_and_tables
from sqlmodel import SQLModel
SQLModel.metadata.drop_all(engine)
create_db_and_tables()
"
```

### Alembic (deferred)

Full migration tooling (Alembic) is **not** introduced in Phase II. Rationale:
the `task` schema is new; there is no existing data to migrate. Alembic will
be introduced in Phase III when schema evolution is required.

---

## Test Database Strategy

Backend unit and integration tests use an **in-memory SQLite** database to
avoid requiring a Neon DB connection during CI runs.

| Setting | Value |
|---------|-------|
| URL | `sqlite:///:memory:` |
| Pool | `StaticPool` (share one connection across threads) |
| Lifecycle | Created fresh for each test session; destroyed on teardown |

The `get_session` FastAPI dependency is overridden in tests via
`app.dependency_overrides`.

---

## Environment Variables

### `backend/.env` (server-side, never committed)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | Neon DB connection string | `postgresql+psycopg2://user:pass@host.neon.tech/db?sslmode=require` |
| `BETTER_AUTH_SECRET` | Shared JWT signing secret (min 32 chars) | `a-long-random-secret-string` |

### `frontend/.env.local` (client-side, never committed)

| Variable | Description | Example |
|----------|-------------|---------|
| `BETTER_AUTH_SECRET` | Same value as backend | `a-long-random-secret-string` |
| `DATABASE_URL` | Same Neon DB (used by Better Auth) | same connection string |
| `NEXT_PUBLIC_APP_URL` | Public URL of the Next.js app | `http://localhost:3000` |
| `NEXT_PUBLIC_API_URL` | FastAPI base URL | `http://localhost:8000` |

---

## Data Integrity Rules

| Rule | Enforcement |
|------|-------------|
| `title` must not be empty after stripping whitespace | Application layer (TaskManager + route handler) |
| `title` ≤ 200 characters | Application layer + SQLModel `max_length` |
| `description` ≤ 500 characters | Application layer + SQLModel `max_length` |
| `user_id` is always set from JWT `sub` — never from request body | Route handler + `get_current_user` dependency |
| A user can only access their own tasks | `WHERE user_id = :user_id` on every query |
| `id` is never reused | PostgreSQL `SERIAL` / `IDENTITY` — auto-increment, never recycled |

---

## References

| Document | Path |
|----------|------|
| Phase II overview | `specs/overview.md` |
| Auth spec | `specs/features/authentication.md` |
| REST endpoints | `specs/api/rest-endpoints.md` |
| UI pages | `specs/ui/pages.md` |
| Phase I feature spec | `specs/features/task-crud.md` |
| Phase I data layer | `src/models.py` |
| Global constitution | `.specify/memory/constitution.md` |
