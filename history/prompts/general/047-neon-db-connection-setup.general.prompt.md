---
id: 047
title: Neon DB Connection Setup and Alembic Migrations
stage: general
date: 2026-02-28
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Connect Neon DB properly. Add Neon connection setup, replace in-memory storage with database-backed storage, create proper schema/migrations, ensure TaskManager unchanged, provide verification instructions."
labels: ["phase-ii", "neon-db", "alembic", "migrations", "postgresql", "database"]
links:
  spec: specs/database/schema.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/src/database.py (modified — Neon pool settings)
  - backend/src/app.py (modified — /health/db endpoint)
  - backend/pyproject.toml (modified — alembic added)
  - backend/.env (modified — Neon URL instructions)
  - backend/.env.example (modified — Neon URL template)
  - backend/alembic.ini (created)
  - backend/alembic/env.py (created)
  - backend/alembic/script.py.mako (created)
  - backend/alembic/versions/001_initial_schema.py (created)
tests:
  - backend/tests/ (203 passing — no regression)
---

## Prompt

Proceed to connect Neon DB properly.

1. Add Neon connection setup.
2. Replace in-memory storage with database-backed storage.
3. Create proper schema/migrations for tasks.
4. Ensure TaskManager remains unchanged (clean architecture).
5. Provide step-by-step verification instructions.

Do not break existing API routes.
Follow production-grade structure.

## Response snapshot

DBTaskStore adapter and SQLModel Task table were already in place. Work focused on:

1. database.py — added Neon-specific pool settings (pool_pre_ping=True, pool_recycle=300, pool_size=5, max_overflow=10) applied only for PostgreSQL; SQLite path unchanged.
2. app.py — added /health/db endpoint that runs SELECT 1 and returns dialect name.
3. pyproject.toml — added alembic>=1.14.0; installed alembic==1.18.4 via uv.
4. Alembic scaffolding created: alembic.ini, alembic/env.py (reads DATABASE_URL from .env, imports Task model for metadata detection), alembic/script.py.mako, alembic/versions/001_initial_schema.py (authoritative CREATE TABLE task DDL with index on user_id).
5. dev.db stamped at revision 001 (table already existed from SQLModel create_all — stamp avoids re-run without losing data).
6. 203 tests pass — no regression.

TaskManager, DBTaskStore, all route handlers: zero changes.

## Outcome

- ✅ Impact: Production-grade Neon DB integration ready. Plug in DATABASE_URL, run `alembic upgrade head`, start server.
- 🧪 Tests: 203 passed — zero regression.
- 📁 Files: 9 files modified/created. TaskManager untouched (clean architecture preserved).
- 🔁 Next prompts: Connect to real Neon instance, run verification checklist §3, rotate BETTER_AUTH_SECRET.
- 🧠 Reflection: pool_pre_ping is critical for Neon — serverless Postgres drops idle connections silently. Without it, the first request after idle time would fail with a connection error. The stamp command (not upgrade) is the correct fix for "table already exists" on an existing dev database.

## Evaluation notes (flywheel)

- Failure modes observed: alembic upgrade head on existing dev.db → OperationalError "table task already exists". Fixed with `alembic stamp 001`.
- Graders run and results (PASS/FAIL): PASS — 203 tests; PASS — alembic current shows 001 (head); PASS — engine dialect confirmed sqlite for dev.
- Prompt variant (if applicable): production-grade database setup
- Next experiment (smallest change to try): Update DATABASE_URL to real Neon URL and run `alembic upgrade head` to verify PostgreSQL migration path end-to-end.
