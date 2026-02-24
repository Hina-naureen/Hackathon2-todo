---
id: "013"
title: Phase II Backend Implementation
stage: green
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: task-api
branch: master
user: pc
command: "Implement backend based on @specs/api/rest-endpoints.md @specs/database/schema.md @specs/features/task-crud.md. Requirements: FastAPI app, SQLModel models, Neon DB connection, CRUD routes, JWT middleware placeholder. Create backend inside /backend folder."
labels: ["phase-2","green","fastapi","sqlmodel","sqlite","neon","jwt","crud","routes","backend"]
links:
  spec: specs/api/rest-endpoints.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/db_models.py
  - backend/src/database.py
  - backend/src/app.py
  - backend/src/routes/__init__.py
  - backend/src/routes/tasks.py
  - backend/src/auth/__init__.py
  - backend/src/auth/dependencies.py
  - backend/.env.example
  - backend/tests/test_api.py
  - backend/pyproject.toml
  - .gitignore
tests:
  - "uv run pytest tests/ -q from backend/ — 144 passed (107 Phase I + 37 Phase II)"
  - "echo 0 | uv run todo — Phase I console boots cleanly"
---

## Prompt

Implement backend based on:

@specs/api/rest-endpoints.md
@specs/database/schema.md
@specs/features/task-crud.md

Requirements:
- FastAPI app
- SQLModel models
- Neon DB connection
- CRUD routes
- JWT middleware placeholder

Create backend inside /backend folder.

## Response snapshot

Added 46 packages via `uv add "fastapi[standard]" sqlmodel psycopg2-binary python-dotenv pyjwt`.

Created 9 new files:

### backend/src/db_models.py
- `Task(SQLModel, table=True)` — 7 columns: id, title, description, completed, user_id, created_at, updated_at
- `TaskCreate` — POST body (title required, description optional)
- `TaskUpdate` — PUT body (both Optional; null = keep existing)
- `TaskRead` — response schema (no user_id exposed)
- `_utcnow()` — naive UTC datetime helper (replaces deprecated `datetime.utcnow()`)

### backend/src/database.py
- `DATABASE_URL` defaults to `sqlite:///./dev.db` if not set in .env
- `engine` with SQLite-specific `check_same_thread=False`
- `create_db_and_tables()` — `SQLModel.metadata.create_all(engine)`
- `get_session()` — FastAPI Depends generator
- `DBTaskStore` — DB-backed adapter; same 4-method interface as Phase I TaskStore (add / get_all / get_by_id / delete); uses `flush()` to get auto-assigned id within transaction without committing

### backend/src/auth/dependencies.py
- `get_current_user` FastAPI dependency
- `AUTH_DISABLED=true` env var bypasses JWT for local dev
- PyJWT HS256 decode with `BETTER_AUTH_SECRET`
- Returns `user_id` from `sub` claim; raises HTTP 401 for missing/expired/invalid tokens

### backend/src/routes/tasks.py
- 6 endpoints matching specs/api/rest-endpoints.md exactly
- `_manager(session, user_id)` helper wires Phase I `TaskManager` with `DBTaskStore`
- Validation in route handlers (empty title → 400, length limits → 400)
- `task.updated_at = _utcnow()` set before commit on update + toggle
- Route handler owns `session.commit()` + `session.refresh(task)` — manager never commits

### backend/src/app.py
- `lifespan` asynccontextmanager calls `create_db_and_tables()` on startup
- CORSMiddleware with `ALLOWED_ORIGINS` env var (defaults to localhost:3000)
- `/api/tasks` router included
- `/health` endpoint

### backend/.env.example
- DATABASE_URL, BETTER_AUTH_SECRET, AUTH_DISABLED, ALLOWED_ORIGINS documented

### backend/tests/test_api.py
- 37 tests across 7 classes
- SQLite StaticPool in-memory engine per test; dependency_overrides for session + user
- User isolation tests use direct DB seeding (`_seed_other_task()`) to avoid fixture conflict
- Auth tests clear dependency_overrides and use bare TestClient to verify 401 behaviour

### One bug encountered and fixed
Three user-isolation tests failed because `client` and `client_other` fixtures both wrote to `app.dependency_overrides` simultaneously (last writer wins). Fixed by replacing `client_other` fixture with `_seed_other_task()` helper that inserts tasks directly into the DB with a different `user_id`. All 3 tests now pass.

## Outcome

- ✅ Impact: Full FastAPI backend implemented; 6 endpoints matching spec; Phase I code unchanged and untouched; console app still boots; SQLite for dev, Neon DB for prod
- 🧪 Tests: 144/144 passed (107 Phase I + 37 Phase II) in 4.67s
- 📁 Files: 9 created, pyproject.toml updated (46 new packages), .gitignore updated (*.db)
- 🔁 Next prompts: Scaffold Next.js frontend in frontend/ → connect to this API
- 🧠 Reflection: The key architectural decision was keeping Phase I's `TaskManager` completely unchanged and passing `DBTaskStore` via duck typing. The `# type: ignore[arg-type]` comments on the wiring call are the only concession to the type system. The route handler owning `session.commit()` keeps the service layer DB-agnostic.

## Evaluation notes (flywheel)

- Failure modes observed: user-isolation tests failed due to shared `app.dependency_overrides` dict when two TestClient fixtures are active simultaneously
- Fix: replaced `client_other` fixture with direct DB seeding helper `_seed_other_task()`
- Graders run and results (PASS/FAIL): pytest 144/144 PASS, boot PASS
- Prompt variant (if applicable): initial
- Next experiment: start the FastAPI server with AUTH_DISABLED=true and manually test all 6 endpoints via Swagger UI at http://localhost:8000/docs
