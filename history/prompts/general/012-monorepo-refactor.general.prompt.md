---
id: "012"
title: Monorepo Refactor
stage: general
date: 2026-02-24
surface: agent
model: claude-sonnet-4-6
feature: none
branch: master
user: pc
command: "Refactor repository into monorepo structure for Phase II. Create folders: frontend/ backend/. Move Python console logic into backend as foundation. Keep Spec-Kit structure intact."
labels: ["monorepo","refactor","phase-2","structure","backend","frontend","phase-1"]
links:
  spec: specs/overview.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/pyproject.toml
  - backend/uv.lock
  - backend/.python-version
  - backend/src/
  - backend/tests/
  - frontend/.gitkeep
  - .gitignore
tests:
  - "uv run pytest tests/ -q from backend/ — 107 passed in 0.69s"
  - "echo 0 | uv run todo from backend/ — boots and exits cleanly"
---

## Prompt

Refactor repository into monorepo structure for Phase II.

Create folders:

frontend/
backend/

Move Python console logic into backend as foundation.

Keep Spec-Kit structure intact.

## Response snapshot

Performed a structural refactoring of the repository from a flat Python project
to a monorepo layout. No application logic was changed.

### Moves

| From | To |
|------|----|
| `src/` | `backend/src/` |
| `tests/` | `backend/tests/` |
| `pyproject.toml` | `backend/pyproject.toml` |
| `uv.lock` | `backend/uv.lock` |
| `.python-version` | `backend/.python-version` |

### Removals

- `main.py` (root) — removed; this was a template stub (`print("Hello from todo-console!")`), not the real app. The real entry point is `backend/src/main.py`.

### Edits

- `backend/pyproject.toml` — removed `readme = "README.md"` field (README.md stays at repo root, not inside `backend/`); all other config unchanged.
- `.gitignore` — added frontend patterns: `node_modules/`, `.next/`, `.vercel/`, `out/`.

### Created

- `frontend/.gitkeep` — placeholder so git tracks the empty `frontend/` directory.
- `backend/.venv` — created by running `uv sync` inside `backend/`.

### Unchanged (Spec-Kit structure intact)

- `specs/` — all spec documents
- `history/prompts/` — all PHRs
- `history/adr/` — ADR directory
- `.specify/` — templates and constitution
- `CLAUDE.md`, `README.md`, `DEMO.md` — root documentation

### Verification

```
uv sync          (from backend/) → 7 packages installed, todo-console 0.1.0 built
uv run pytest    (from backend/) → 107 passed in 0.69s
echo 0 | uv run todo             → boots, prints menu, exits "Goodbye!"
```

## Outcome

- ✅ Impact: Monorepo layout established; Phase I console app fully functional from backend/; frontend/ ready for Next.js scaffold; Spec-Kit structure untouched
- 🧪 Tests: 107/107 passed from backend/ — no regressions
- 📁 Files: backend/{src/,tests/,pyproject.toml,uv.lock,.python-version}, frontend/.gitkeep, .gitignore (updated)
- 🔁 Next prompts: Scaffold backend FastAPI layer → add FastAPI + SQLModel + psycopg2 deps → implement routes (green)
- 🧠 Reflection: Only the `readme = "README.md"` field needed to be removed from pyproject.toml — all entry points, test paths, and build config continued to work unchanged after the move.

## Evaluation notes (flywheel)

- Failure modes observed: none — all moves succeeded; tests green on first run
- Graders run and results (PASS/FAIL): pytest 107/107 PASS, boot PASS
- Prompt variant (if applicable): initial
- Next experiment: scaffold frontend/ with `npx create-next-app@latest . --typescript --app --tailwind --src-dir` from frontend/ and verify Next.js dev server boots
